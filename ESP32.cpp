#include <esp_now.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <esp_wifi.h> 

#define WORKER_TIMEOUT_MS 60000 
#define ULTRASONIC_PIN 25
#define EXPECTED_NODES 2
#define TRIGGER_RESET_AFTER 10
#define SLEEP_TIME_SEC 5
#define BATTERY_PIN 32
#define LOOPS_ON_DUTY 100
const char* ssid = "";

const char* password = ""; 
const char* serverURL = ""; 

enum NodeState {
  STATE_DISCOVERY = 0,
  STATE_ELECTION = 1,
  STATE_WORKER = 2,
  STATE_HEAD = 3
};

enum MsgType : uint8_t {
  DISCOVERY = 1,
  VOTE_RSSI = 2,
  SENSOR_DATA = 3,
  HEAD_READY = 4, 
  GO_SLEEP = 5,
  UPDATE_NETWORK = 6,
  RESTART = 7
};

typedef struct { //For discovery phase
  uint8_t mac[6];
  int32_t rssi_score;
  float batteryVoltage;
} PeerInfo;

typedef struct { 
  uint8_t mac[6];
  float distance;
  unsigned long lastOnTimeMs;
  float batteryVoltage;
  bool readyToUpload;
  uint64_t chipId;
} DataBuffer;

typedef struct {
  float distance;
  unsigned long lastOnTimeMs; 
  float batteryVoltage; 
  uint64_t chipId; 
} SensorPayload;

typedef struct{
  uint8_t newMac[6];
  PeerInfo peers[EXPECTED_NODES];
} UpdatePayload;

typedef struct{
  int32_t voteRSSI;
  float batteryVoltage;
}voteInfo;
typedef struct {
  MsgType type;
  union {
    UpdatePayload updatePayload;
    voteInfo vote; 
    SensorPayload sensor;       
    unsigned long sleepSeconds; 
  } payload;
} Packet;

Packet outgoingMsg;
uint8_t broadcastAddr[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
uint8_t myMac[6];
DataBuffer uploadQueue[EXPECTED_NODES];
bool headIsReady = false;
bool shouldSleep = false;
volatile int votesCounted = 0; 
int loopsWithOutSleeping = 0; 
esp_now_peer_info_t espPeerInfo;

RTC_DATA_ATTR unsigned long lastCycle = 0; 
RTC_DATA_ATTR int loopsAsHead = 0;
RTC_DATA_ATTR uint8_t headMac[6]; 
RTC_DATA_ATTR PeerInfo peers[EXPECTED_NODES]; 
RTC_DATA_ATTR NodeState currentState = STATE_DISCOVERY;
RTC_DATA_ATTR int peerCount = 0;

void runDiscovery();
void runElection();
void runWorker();
void runHead();
int32_t getStrength(); 
void registerPeer(const uint8_t *mac);
void OnDataRecv(const esp_now_recv_info_t * info, const uint8_t *incomingData, int len);
void OnDataSent(const wifi_tx_info_t *info, esp_now_send_status_t status);
float measureDistance();
void formatMacAddress(const uint8_t *macAddr, char *buffer, int maxLength);

float readBatteryVoltage() {
    const float R1 = 100000.0;  
    const float R2 = 100000.0;  
    const float ADC_MAX = 4095.0;
    const float VREF = 3.3;    

    int raw = analogRead(BATTERY_PIN);

    if (raw <= 0 || raw >= 4095) {
        return 0.0;    
    }

    float adcVoltage = (raw / ADC_MAX) * VREF;

    float batteryVoltage = adcVoltage * ((R1 + R2) / R2);

    if (batteryVoltage < 3.0 || batteryVoltage > 8.0) {
        return 0.0;
    }

    return batteryVoltage;
}

void setup(){

  Serial.begin(115200);
  Serial.println("Starting ESP");

  WiFi.mode(WIFI_STA);
  esp_wifi_set_promiscuous(true);
  esp_wifi_set_channel(1, WIFI_SECOND_CHAN_NONE);
  esp_wifi_set_promiscuous(false);

  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP-NOW Init Failed");
    ESP.restart();
  }
 
  esp_now_register_recv_cb(OnDataRecv);
  esp_now_register_send_cb(OnDataSent);

  registerPeer(broadcastAddr);
  Serial.print("Boot State: ");
  Serial.println(currentState);

  for(int i=0; i<EXPECTED_NODES; i++) uploadQueue[i].readyToUpload = false;
  WiFi.macAddress(myMac);
}

void loop(){
  loopsWithOutSleeping += 1;
  switch(currentState){
    case STATE_DISCOVERY:
      runDiscovery();
      break;
    case STATE_ELECTION:
      runElection();
      break;
    case STATE_WORKER:
      runWorker();
      break;
    case STATE_HEAD:
      runHead();
      break;
  }
  delay(100);
  if(loopsWithOutSleeping > TRIGGER_RESET_AFTER){
    currentState = STATE_DISCOVERY;
  }
}
void runDiscovery(){

  Serial.println("Discovery CAPTAIN");
  unsigned long lastMsg = 0; 
  unsigned long timeOut = millis();
  while (peerCount < EXPECTED_NODES && millis() - timeOut < WORKER_TIMEOUT_MS){
    if(millis() - lastMsg > 3000){
      lastMsg = millis();
      Serial.print("Trying to join the crew: ");
      Serial.println(peerCount);
      outgoingMsg.type = DISCOVERY;
      esp_now_send(broadcastAddr, (uint8_t*)&outgoingMsg, sizeof(outgoingMsg));
    }
    delay(100);
  }
  Serial.println("Crew assembled");
  unsigned long delayPeriod = millis();

  while (millis() - delayPeriod < 5000) {
    if (millis() - lastMsg > 1000) {
      lastMsg = millis();
      outgoingMsg.type = DISCOVERY;
      esp_now_send(broadcastAddr, (uint8_t*)&outgoingMsg, sizeof(outgoingMsg));
    }
    delay(100);
  }
  currentState = STATE_ELECTION;
}

void runElection(){
  Serial.println("Electing Captain!");
  int32_t myRSSI = getStrength();
  float myBatteryVoltage = readBatteryVoltage();
  outgoingMsg.type = VOTE_RSSI; 
  outgoingMsg.payload.vote.batteryVoltage = myBatteryVoltage;
  outgoingMsg.payload.vote.voteRSSI = myRSSI;
  esp_now_send(broadcastAddr, (uint8_t*)&outgoingMsg, sizeof(outgoingMsg));

  for(int i=0; i<peerCount; i++) {
    peers[i].rssi_score = -999; 
    peers[i].batteryVoltage = 0;
  }

  unsigned long start = millis();
  while((millis() - start < 10000) && votesCounted < peerCount){
    esp_now_send(broadcastAddr, (uint8_t*)&outgoingMsg, sizeof(outgoingMsg));
    delay(500);
  }
  bool elected = (myRSSI > -70);
  bool iAmTheBest = true;
  int32_t tempRSSI = myRSSI;
  float tempbattery = myBatteryVoltage;
  uint8_t best_mac[6];
  memcpy(best_mac, myMac, 6);
  
  for(int i=0; i<peerCount; i++){
    if(peers[i].rssi_score > -70){
      elected = true;
      if(peers[i].batteryVoltage > tempbattery){
        tempbattery = peers[i].batteryVoltage;
        iAmTheBest = false;
        memcpy(best_mac, peers[i].mac, 6);
        memcpy(headMac, peers[i].mac, 6);
      }else if(peers[i].batteryVoltage == tempbattery && memcmp(peers[i].mac, best_mac, 6) > 0){
        iAmTheBest = false;
        memcpy(best_mac, peers[i].mac, 6);
        memcpy(headMac, peers[i].mac, 6);
      }
    }
  }
  
  if (!elected){
  for(int i=0; i<peerCount; i++) {
    if (peers[i].rssi_score > tempRSSI) {
      tempRSSI = peers[i].rssi_score;
      iAmTheBest = false;
      memcpy(best_mac, peers[i].mac, 6);
      memcpy(headMac, peers[i].mac, 6);
    } 
    else if (peers[i].rssi_score == tempRSSI) {
       if (memcmp(peers[i].mac, best_mac, 6) > 0) {
          iAmTheBest = false;
          memcpy(best_mac, peers[i].mac, 6);
          memcpy(headMac, peers[i].mac, 6);
      }
    }
  }
  }

  if (iAmTheBest) {
    Serial.println("I AM THE CAPTaIN NOW");
    memcpy(headMac, myMac, 6);
    currentState = STATE_HEAD;
    
    outgoingMsg.type = GO_SLEEP;
    outgoingMsg.payload.sleepSeconds = SLEEP_TIME_SEC;
    for(int k=0; k<3; k++) {
        esp_now_send(broadcastAddr, (uint8_t*)&outgoingMsg, sizeof(outgoingMsg));
        delay(20);
    }
  } else {
    Serial.println("I am a crewmate");
    currentState = STATE_WORKER;
    
    unsigned long waitStart = millis();
    while(millis() - waitStart < 5000) {
      delay(10);
    }
  }
}

void runHead(){
  Serial.println("Running Head");
  
  outgoingMsg.type = HEAD_READY; 
  esp_now_send(broadcastAddr, (uint8_t*)&outgoingMsg, sizeof(outgoingMsg));
  float myDistance = measureDistance();
  float myBattery = readBatteryVoltage();
  unsigned long myOnTime = lastCycle;
  unsigned long length = millis();

  while(millis() - length < 3000){
    int ready = 0;
    for (int i = 0; i < EXPECTED_NODES; i++) {
      if (uploadQueue[i].readyToUpload) ready++;
    }
    if (ready == EXPECTED_NODES) { 
      break;
    }
    delay(30);
  }

  WiFi.begin(ssid, password); 
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi Connected");
    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");
    char jsonBuffer[1024];
    strcpy(jsonBuffer, "["); 
    
    char nodeJson[200];
    char macStr[18];
    bool firstItem = true;

    for(int i=0; i<EXPECTED_NODES; i++) {
      if(uploadQueue[i].readyToUpload) {
        if (!firstItem) strcat(jsonBuffer, ",");
        
        formatMacAddress(uploadQueue[i].mac, macStr, 18);
        snprintf(nodeJson, sizeof(nodeJson), 
        "{\"node_mac\":\"%s\", \"distance\":%.2f, \"uptime_ms\":%lu, \"battery\":%.2f, \"role\":\"WORKER\", \"chip_id\":%u}", 
        macStr, uploadQueue[i].distance, uploadQueue[i].lastOnTimeMs, uploadQueue[i].batteryVoltage, uploadQueue[i].chipId);
        
        strcat(jsonBuffer, nodeJson);
        firstItem = false;
      }
    }

    if (!firstItem) strcat(jsonBuffer, ",");
    String myMacStr = WiFi.macAddress(); 
    snprintf(nodeJson, sizeof(nodeJson), 
             "{\"node_mac\":\"%s\", \"distance\":%.2f, \"uptime_ms\":%lu, \"battery\":%.2f, \"role\":\"HEAD\", \"chip_id\":%u}", 
             myMacStr.c_str(), myDistance, myOnTime, myBattery, ESP.getEfuseMac());
    strcat(jsonBuffer, nodeJson);

    strcat(jsonBuffer, "]");

    int httpCode = http.POST(jsonBuffer);
    if (httpCode > 0) {
      Serial.printf("Batch Upload Success: %d\n", httpCode);
    } else {
      Serial.printf("Batch Upload Failed: %s\n", http.errorToString(httpCode).c_str());
    }
    http.end();

  } else {
    Serial.println("WiFi Fail. Skipping upload.");
  }

  Serial.println("Phase 3: Switching back to Ch1 to Dismiss Workers...");
  WiFi.disconnect(); 
  delay(100); 
  esp_wifi_set_promiscuous(true);
  esp_wifi_set_channel(1, WIFI_SECOND_CHAN_NONE);
  esp_wifi_set_promiscuous(false);
  loopsAsHead++;
  if(loopsAsHead >= LOOPS_ON_DUTY){
    delay(50);
    outgoingMsg.type = RESTART;
    outgoingMsg.payload.sleepSeconds = SLEEP_TIME_SEC;
    Serial.println("Restarting to relect");
    esp_now_send(broadcastAddr, (uint8_t*)&outgoingMsg, sizeof(outgoingMsg));
    delay(50);
    lastCycle = 0; 
    loopsAsHead = 0;
    memset(headMac, 0, 6);
    memset(peers, 0, sizeof(peers));
    currentState = STATE_DISCOVERY;
    peerCount = 0;
  }else{
  outgoingMsg.type = GO_SLEEP;
  outgoingMsg.payload.sleepSeconds = SLEEP_TIME_SEC;
  esp_now_send(broadcastAddr, (uint8_t*)&outgoingMsg, sizeof(outgoingMsg));
  delay(50);
  }
  Serial.flush(); 
  lastCycle = millis();
  esp_sleep_enable_timer_wakeup(SLEEP_TIME_SEC * 1000000);
  esp_deep_sleep_start(); 
}

void runWorker(){
  Serial.println("StartingWorker");
 
  unsigned long startWait = millis();
  while (!headIsReady) {

    if (millis() - startWait > WORKER_TIMEOUT_MS) {
      Serial.println("reseting state");
      ESP.restart();
      return;
    }
    delay(10); 
  }

  Serial.println("Head is Ready! Measuring...");
  float dist = measureDistance();
  registerPeer(headMac);
  outgoingMsg.type = SENSOR_DATA;
  outgoingMsg.payload.sensor.distance = dist;
  outgoingMsg.payload.sensor.lastOnTimeMs = lastCycle; 
  outgoingMsg.payload.sensor.batteryVoltage = readBatteryVoltage(); 
  outgoingMsg.payload.sensor.chipId = ESP.getEfuseMac();


  esp_now_send(headMac, (uint8_t*)&outgoingMsg, sizeof(outgoingMsg));

  startWait = millis();
  while (millis()- startWait < 5000) {
    delay(50);
  }
  Serial.println("Issue this worker node is returning");
}

void registerPeer(const uint8_t *mac) {
  memset(&espPeerInfo, 0, sizeof(espPeerInfo));
  memcpy(espPeerInfo.peer_addr, mac, 6);
  espPeerInfo.channel = 1;
  espPeerInfo.encrypt = false;
  esp_now_add_peer(&espPeerInfo);
}
int32_t getStrength(){
  int n = WiFi.scanNetworks();
  for(int i =0; i<n; ++i){
    if(String(WiFi.SSID(i)) == String(ssid)) return WiFi.RSSI(i);
  }
  return -100;
}
float measureDistance() {
  pinMode(ULTRASONIC_PIN, OUTPUT);
  digitalWrite(ULTRASONIC_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(ULTRASONIC_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(ULTRASONIC_PIN, LOW);
  pinMode(ULTRASONIC_PIN, INPUT);
  long duration = pulseIn(ULTRASONIC_PIN, HIGH);
  float cm = duration / 29.1 / 2.0;
  Serial.print("Distance: "); Serial.println(cm);
  return cm; 
}
void formatMacAddress(const uint8_t *macAddr, char *buffer, int maxLength) {
  snprintf(buffer, maxLength, "%02X:%02X:%02X:%02X:%02X:%02X", 
           macAddr[0], macAddr[1], macAddr[2], macAddr[3], macAddr[4], macAddr[5]);
}

void OnDataRecv(const esp_now_recv_info_t * info, const uint8_t *incomingData, int len) {
  if (len != sizeof(Packet)) return;
  Packet incomingMsg;
  memcpy(&incomingMsg, incomingData, len);

  bool known = false; 
  for(int i=0; i<peerCount; i++){
    if (memcmp(peers[i].mac, info->src_addr, 6) == 0) known = true;
  }

  if (!known && peerCount < EXPECTED_NODES) {
    Serial.println("Unknown peer detected! Adding to list...");
    memcpy(peers[peerCount].mac, info->src_addr, 6);
    peers[peerCount].rssi_score = -999; 
    peers[peerCount].batteryVoltage = 0;
    registerPeer(peers[peerCount].mac); 
    peerCount++;
  }

  switch(incomingMsg.type){
    case DISCOVERY: 
      Serial.println("Got discovery!");
      Packet reply;
      if(currentState == STATE_HEAD){
        Packet reply = {};  
        reply.type = UPDATE_NETWORK;

        memcpy(reply.payload.updatePayload.newMac, info->src_addr, 6);
        memcpy(reply.payload.updatePayload.peers, peers, sizeof(peers));

        Serial.println("Sending update");
        esp_now_send(broadcastAddr, (uint8_t*)&reply, sizeof(Packet));
      }
      break;

    case UPDATE_NETWORK:
      
      Serial.println("Got Network Update!");
      if(memcmp(myMac, incomingMsg.payload.updatePayload.newMac, 6) == 0){
        currentState = STATE_WORKER;
        memcpy(headMac, info->src_addr, 6);
        if(peerCount < EXPECTED_NODES){
        for(int i=0; i< EXPECTED_NODES; i++){
          if(memcmp(myMac, incomingMsg.payload.updatePayload.peers[i].mac, 6) != 0){
            memcpy(peers[EXPECTED_NODES-1].mac, incomingMsg.payload.updatePayload.peers[i].mac, 6);
            peers[EXPECTED_NODES-1].rssi_score = incomingMsg.payload.updatePayload.peers[i].rssi_score;
            peers[EXPECTED_NODES-1].batteryVoltage = 0;
            peerCount++;          
          }
        }}
        Serial.println("Restarting");
        esp_sleep_enable_timer_wakeup(1000000);
        esp_deep_sleep_start();
      }else if(peerCount < EXPECTED_NODES){
        memcpy(peers[EXPECTED_NODES-1].mac, incomingMsg.payload.updatePayload.newMac, 6);
        peers[EXPECTED_NODES-1].rssi_score = -999;
        peers[EXPECTED_NODES-1].batteryVoltage = 0;
        peerCount++;
      }
      break;
 
    case VOTE_RSSI:
      if(currentState == STATE_ELECTION){
      Serial.println("Got a Vote");
        for(int i=0; i<peerCount; i++){
          if (memcmp(peers[i].mac, info->src_addr, 6) == 0) {
            Serial.println("Vote Counted");
            peers[i].rssi_score = incomingMsg.payload.vote.voteRSSI;
            peers[i].batteryVoltage = incomingMsg.payload.vote.batteryVoltage;
            votesCounted++;
          }
      } }
      break;
    case HEAD_READY:
      Serial.println("Head's ready");
      if (currentState == STATE_HEAD){
        currentState = STATE_DISCOVERY; 
        esp_sleep_enable_timer_wakeup(1000000);
        esp_deep_sleep_start();
      }
      headIsReady = true;
      break;

    case GO_SLEEP:
      if(currentState == STATE_WORKER){
        Serial.println("Going to Sleep");
        lastCycle = millis();
        esp_sleep_enable_timer_wakeup(SLEEP_TIME_SEC * 1000000);
        esp_deep_sleep_start();
      }else{
        currentState = STATE_DISCOVERY;
        esp_sleep_enable_timer_wakeup(1000000);
        esp_deep_sleep_start();
      }
      break; 
    case SENSOR_DATA:
      if(currentState == STATE_HEAD){
        for(int i=0; i<EXPECTED_NODES; i++) {
          if(!uploadQueue[i].readyToUpload || memcmp(uploadQueue[i].mac, info->src_addr, 6) == 0) {
            Serial.println("Got sensorData");
            memcpy(uploadQueue[i].mac, info->src_addr, 6);
            uploadQueue[i].distance = incomingMsg.payload.sensor.distance;
            uploadQueue[i].lastOnTimeMs = incomingMsg.payload.sensor.lastOnTimeMs;
            uploadQueue[i].batteryVoltage = incomingMsg.payload.sensor.batteryVoltage;
            uploadQueue[i].readyToUpload = true;
            uploadQueue[i].chipId = incomingMsg.payload.sensor.chipId;
            break;
          }
        }
    }
    break;
    case RESTART: 
      lastCycle = 0; 
      loopsAsHead = 0;
      memset(headMac, 0, 6);
      memset(peers, 0, sizeof(peers));
      currentState = STATE_DISCOVERY;
      peerCount = 0;
      lastCycle = millis();
      esp_sleep_enable_timer_wakeup(SLEEP_TIME_SEC * 1000000);
      esp_deep_sleep_start();

  }
}
void OnDataSent(const wifi_tx_info_t *info, esp_now_send_status_t status) {}
