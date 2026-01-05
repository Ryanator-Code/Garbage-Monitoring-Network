import { useState, useEffect } from 'react'
import './App.css'
import { getAllNodes, getNodeData, updateNodeName, getSystemStatus } from './api'
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts'

const BIN_BASELINES = {
    "823C": 30.8,
    "8AB8": 38.3,
    "9D58": 37.9
}

const WifiHighIcon = ({ className }) => (
    <svg
        className={className}
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
    >
        <g>
            <path
                d="M8.34277 14.5899C8.80861 14.0903 9.37187 13.6915 9.9978 13.418C10.6237 13.1446 11.2995 13.0025 11.9826 13.0001C12.6656 12.9977 13.3419 13.1353 13.9697 13.4044C14.5975 13.6735 15.1637 14.0683 15.633 14.5646M6.14941 11.5439C6.89476 10.7446 7.79597 10.1066 8.79745 9.66902C9.79893 9.23148 10.8793 9.00389 11.9721 9.00007C13.065 8.99626 14.1466 9.21651 15.1511 9.64704C16.1556 10.0776 17.0617 10.7094 17.8127 11.5035M3.22363 8.81635C4.34165 7.61742 5.69347 6.66028 7.19569 6.00398C8.69791 5.34768 10.3179 5.0058 11.9572 5.00007C13.5966 4.99435 15.2208 5.32472 16.7276 5.97052C18.2344 6.61632 19.5931 7.56458 20.7195 8.75568M12 19.0001C11.4477 19.0001 11 18.5524 11 18.0001C11 17.4478 11.4477 17.0001 12 17.0001C12.5523 17.0001 13 17.4478 13 18.0001C13 18.5524 12.5523 19.0001 12 19.0001Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </g>
    </svg>
)

const WifiMediumIcon = ({ className }) => (
    <svg
        className={className}
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
    >
        <g>
            <path
                d="M8.34375 14.5898C8.80959 14.0903 9.37285 13.6915 9.99877 13.418C10.6247 13.1446 11.2995 13.0024 11.9826 13C12.6656 12.9977 13.3418 13.1353 13.9697 13.4044C14.5975 13.6735 15.1637 14.0683 15.633 14.5646M6.14941 11.5439C6.89476 10.7446 7.79597 10.1065 8.79745 9.66899C9.79893 9.23146 10.8802 9.00386 11.9731 9.00005C13.066 8.99623 14.1475 9.21648 15.1521 9.64701C16.1566 10.0775 17.0617 10.7084 17.8127 11.5025M12 19C11.4477 19 11 18.5523 11 18C11 17.4478 11.4477 17 12 17C12.5523 17 13 17.4478 13 18C13 18.5523 12.5523 19 12 19Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </g>
    </svg>
)

const StarIcon = ({ className }) => (
    <svg
        className={className}
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
    >
        <g>
            <path
                d="M2.33496 10.3368C2.02171 10.0471 2.19187 9.52339 2.61557 9.47316L8.61914 8.76107C8.79182 8.74059 8.94181 8.63215 9.01465 8.47425L11.5469 2.98446C11.7256 2.59703 12.2764 2.59695 12.4551 2.98439L14.9873 8.47413C15.0601 8.63204 15.2092 8.74077 15.3818 8.76124L21.3857 9.47316C21.8094 9.52339 21.9791 10.0472 21.6659 10.3369L17.2278 14.4419C17.1001 14.56 17.0433 14.7357 17.0771 14.9063L18.255 20.8359C18.3382 21.2544 17.8928 21.5787 17.5205 21.3703L12.2451 18.4166C12.0934 18.3317 11.9091 18.3321 11.7573 18.417L6.48144 21.3695C6.10913 21.5779 5.66294 21.2544 5.74609 20.8359L6.92414 14.9066C6.95803 14.7361 6.90134 14.5599 6.77367 14.4419L2.33496 10.3368Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </g>
    </svg>
)

function App() {
    const [nodes, setNodes] = useState([])
    const [selectedNode, setSelectedNode] = useState(null)
    const [nodeLogs, setNodeLogs] = useState([])
    const [loading, setLoading] = useState(true)
    const [editingName, setEditingName] = useState(false)
    const [nameInput, setNameInput] = useState('')
    const [savingName, setSavingName] = useState(false)
    const [currentTime, setCurrentTime] = useState(Date.now())
    const [avgCycleUptimeMs, setAvgCycleUptimeMs] = useState(null)

    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentTime(Date.now())
        }, 1000)
        return () => clearInterval(timer)
    }, [])

    useEffect(() => {
        const fetchNodes = async () => {
            setLoading(true)
            const data = await getAllNodes()
            setNodes(data)
            setLoading(false)
        }
        fetchNodes()

        const interval = setInterval(fetchNodes, 3000)
        return () => clearInterval(interval)
    }, [])

    useEffect(() => {
        const fetchStatus = async () => {
            const status = await getSystemStatus()
            if (status && typeof status.avgCycleUptimeMs === 'number') {
                setAvgCycleUptimeMs(status.avgCycleUptimeMs)
            } else {
                setAvgCycleUptimeMs(null)
            }
        }
        fetchStatus()
        const interval = setInterval(fetchStatus, 3000)
        return () => clearInterval(interval)
    }, [])

    useEffect(() => {
        if (!selectedNode) {
            setNodeLogs([])
            return
        }

        const fetchLogs = async () => {
            const data = await getNodeData(selectedNode.chipId)
            setNodeLogs(data.slice(-20))
        }
        fetchLogs()

        const interval = setInterval(fetchLogs, 2000)
        return () => clearInterval(interval)
    }, [selectedNode])

    const handleNodeSelect = (node) => {
        setSelectedNode(node)
        setEditingName(false)
        setNameInput(node.name || '')
    }

    const handleSaveName = async () => {
        if (!selectedNode || !nameInput.trim()) return

        setSavingName(true)
        const result = await updateNodeName(selectedNode.chipId, nameInput.trim())
        setSavingName(false)

        if (result.success) {
            const updatedNodes = nodes.map(n =>
                n.chipId === selectedNode.chipId ? { ...n, name: result.name } : n
            )
            setNodes(updatedNodes)
            setSelectedNode({ ...selectedNode, name: result.name })
            setEditingName(false)
        }
    }

    const handleCancelEdit = () => {
        setNameInput(selectedNode.name || '')
        setEditingName(false)
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            handleSaveName()
        } else if (e.key === 'Escape') {
            handleCancelEdit()
        }
    }

    const handleMapNodeClick = (chipId) => {
        const node = nodes.find(n => n.chipId === chipId)
        if (node) {
            setSelectedNode(node)
        }
    }

    const formatTime = (timestamp) => {
        const date = new Date(timestamp)
        return date.toLocaleTimeString('en-US', { hour12: false })
    }

    const calculateRealTimeUptime = (node) => {
        if (!node || !node.lastUpdate || !node.uptimeMs) return null

        const lastUpdateTime = new Date(node.lastUpdate).getTime()

        const elapsedMs = currentTime - lastUpdateTime

        const realTimeUptimeMs = node.uptimeMs + elapsedMs

        return realTimeUptimeMs
    }

    const formatUptime = (uptimeMs) => {
        if (!uptimeMs) return 'N/A'
        const seconds = Math.floor(uptimeMs / 1000)
        const minutes = Math.floor(seconds / 60)
        const hours = Math.floor(minutes / 60)
        const days = Math.floor(hours / 24)

        if (days > 0) return `${days}d ${hours % 24}h`
        if (hours > 0) return `${hours}h ${minutes % 60}m`
        if (minutes > 0) return `${minutes}m ${seconds % 60}s`
        return `${seconds}s`
    }

    const formatUptimeMs = (uptimeMs) => {
        if (uptimeMs == null) return 'N/A'
        const rounded = Math.max(0, Math.floor(uptimeMs))
        return `${rounded} ms`
    }

    const totalNodes = nodes.length
    const headNode = nodes.find(n => n.role === 'HEAD')
    const onlineNodes = nodes.filter(n => n.uptimeStatus?.state === 'online').length
    const avgBattery = nodes.length > 0
        ? (nodes.reduce((sum, n) => sum + n.battery, 0) / nodes.length).toFixed(1)
        : 0

    const headRealTimeUptime = headNode ? calculateRealTimeUptime(headNode) : null
    const systemUptime = headNode?.uptimeStatus?.state === 'online'
        ? formatUptime(headRealTimeUptime)
        : 'OFFLINE'
    const systemStatus = headNode?.uptimeStatus?.state === 'online' ? 'online' : 'offline'

    const renderUptimeBadge = (node) => {
        if (!node.uptimeStatus) return null

        const { state } = node.uptimeStatus

        if (state === 'offline') {
            return (
                <span className="stat-badge uptime-offline">
                    OFFLINE
                </span>
            )
        } else {
            const realTimeUptime = calculateRealTimeUptime(node)
            return (
                <span className="stat-badge uptime-online">
                    Uptime: {formatUptime(realTimeUptime)}
                </span>
            )
        }
    }

    return (
        <div className="dashboard">
            {/* Top Banner */}
            <header className="top-banner">
                <div className="banner-content">
                    <div className="logo">
                        <WifiHighIcon />
                    </div>
                    <h1 className="app-title">Wireless Sensor Network</h1>
                </div>
            </header>

            {/* Left Sidebar - Sensor List */}
            <aside className="sensor-list">
                <h2>Sensor Nodes</h2>
                <div className="sensor-items">
                    {loading ? (
                        <div className="loading">Loading nodes...</div>
                    ) : nodes.length === 0 ? (
                        <div className="no-nodes">No nodes found</div>
                    ) : (
                        nodes.map(node => {
                            // Check if fill level is critical (>80%)
                            const isFillCritical = node.distance != null && 
                                ['823C', '8AB8', '9D58'].includes(node.chipId.toUpperCase())
                                ? ((BIN_BASELINES[node.chipId.toUpperCase()] - node.distance) / BIN_BASELINES[node.chipId.toUpperCase()]) * 100 > 80
                                : false;
                            
                            return (
                            <div
                                key={node.chipId}
                                className={`sensor-item ${selectedNode?.chipId === node.chipId ? 'active' : ''}`}
                                onClick={() => handleNodeSelect(node)}
                            >
                                <div className="sensor-icon">
                                    {node.role === 'HEAD' ? (
                                        <StarIcon />
                                    ) : (
                                        <WifiHighIcon />
                                    )}
                                </div>
                                <div className="sensor-info">
                                    <div className="sensor-id">{node.name || `Node ${node.chipId.slice(-2)}`}</div>
                                    <div className="sensor-mac">{node.chipId}</div>
                                    <div className="sensor-role">
                                        {node.role}
                                        {isFillCritical && <span className="fill-alert">Full</span>}
                                    </div>
                                </div>
                                <div className={`status-indicator ${node.uptimeStatus?.state === 'online' ? 'online' : 'offline'}`}></div>
                            </div>
                            )
                        })
                    )}
                </div>
            </aside>

            {/* Main Content - Sensor Details */}
            <main className="main-content">
                <div className="content-header">
                    <div className="header-top">
                        <div className="name-section">
                            {selectedNode && editingName ? (
                                <div className="name-edit">
                                    <input
                                        type="text"
                                        value={nameInput}
                                        onChange={(e) => setNameInput(e.target.value)}
                                        onKeyDown={handleKeyDown}
                                        placeholder="Enter node name"
                                        autoFocus
                                        disabled={savingName}
                                    />
                                    <button onClick={handleSaveName} disabled={savingName}>
                                        {savingName ? 'Saving...' : 'Save'}
                                    </button>
                                    <button onClick={handleCancelEdit} disabled={savingName}>
                                        Cancel
                                    </button>
                                </div>
                            ) : (
                                <>
                                    {selectedNode ? (
                                        <h1 onClick={() => setEditingName(true)} className="node-name-clickable">
                                            {selectedNode.name || 'Unnamed Node'}
                                        </h1>
                                    ) : (
                                        <h1>Select a sensor to view details</h1>
                                    )}
                                </>
                            )}
                        </div>
                        {selectedNode && (
                            <div className="chip-id-badge">
                                {selectedNode.chipId}
                            </div>
                        )}
                    </div>

                    {selectedNode && (
                        <div className="node-stats">
                            <span className="stat-badge">Distance: {selectedNode.distance}cm</span>
                            <span className="stat-badge">Battery: {selectedNode.battery}V</span>
                            <span className="stat-badge">{selectedNode.role}</span>
                            {renderUptimeBadge(selectedNode)}
                            {selectedNode.distance != null && 
                             BIN_BASELINES[selectedNode.chipId.toUpperCase()] &&
                             (((BIN_BASELINES[selectedNode.chipId.toUpperCase()] - selectedNode.distance) / BIN_BASELINES[selectedNode.chipId.toUpperCase()]) * 100 > 80) && (
                                <span className="fill-alert">Full</span>
                            )}
                        </div>
                    )}
                </div>
                <div className="data-section">
                    {/* Charts */}
                    <div className="charts-container">
                        {selectedNode && nodeLogs.length > 0 ? (
                            <>
                                <div className="chart-item">
                                    <h4>Bin Fill Level</h4>
                                    <ResponsiveContainer width="100%" height={280}>
                                        <LineChart data={nodeLogs}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                                            <XAxis
                                                dataKey="timestamp"
                                                tick={{ fontSize: 12, fill: '#8b949e' }}
                                                tickFormatter={(time) => formatTime(time)}
                                            />
                                            <YAxis
                                                label={{ value: 'Fill Level (%)', angle: -90, position: 'insideLeft' }}
                                                tick={{ fontSize: 12, fill: '#8b949e' }}
                                                domain={[0, 100]}
                                            />
                                            <Tooltip
                                                contentStyle={{
                                                    backgroundColor: '#161b22',
                                                    border: '1px solid #30363d',
                                                    borderRadius: '6px'
                                                }}
                                                labelStyle={{ color: '#c9d1d9' }}
                                                formatter={(value) => [value != null ? value.toFixed(1) + '%' : 'N/A', 'Fill Level']}
                                                labelFormatter={(label) => formatTime(label)}
                                            />
                                            <Line
                                                type="monotone"
                                                dataKey="fill_percentage"
                                                stroke="#58a6ff"
                                                dot={false}
                                                strokeWidth={2}
                                                isAnimationActive={false}
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>

                                <div className="chart-item">
                                    <h4>Battery Over Time</h4>
                                    <ResponsiveContainer width="100%" height={280}>
                                        <LineChart data={nodeLogs}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                                            <XAxis
                                                dataKey="timestamp"
                                                tick={{ fontSize: 12, fill: '#8b949e' }}
                                                tickFormatter={(time) => formatTime(time)}
                                            />
                                            <YAxis
                                                label={{ value: 'Battery (V)', angle: -90, position: 'insideLeft' }}
                                                tick={{ fontSize: 12, fill: '#8b949e' }}
                                            />
                                            <Tooltip
                                                contentStyle={{
                                                    backgroundColor: '#161b22',
                                                    border: '1px solid #30363d',
                                                    borderRadius: '6px'
                                                }}
                                                labelStyle={{ color: '#c9d1d9' }}
                                                formatter={(value) => [value.toFixed(2) + ' V', 'Battery']}
                                                labelFormatter={(label) => formatTime(label)}
                                            />
                                            <Line
                                                type="monotone"
                                                dataKey="battery"
                                                stroke="#3fb950"
                                                dot={false}
                                                strokeWidth={2}
                                                isAnimationActive={false}
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            </>
                        ) : (
                            <div className="no-selection">
                                {selectedNode
                                    ? 'No data available for this node'
                                    : 'Select a sensor from the left panel or network map to view graphs'}
                            </div>
                        )}
                    </div>

                    {/* Logs */}
                    <div className="logs-section">
                        <h3>Sensor Data Stream</h3>
                        <div className="log-container">
                            {selectedNode ? (
                                nodeLogs.length === 0 ? (
                                    <div className="no-selection">No data available for this node</div>
                                ) : (
                                    <div className="log-entries">
                                         {nodeLogs.map((log, idx) => (
                                             <div key={idx} className="log-entry">
                                                 [{formatTime(log.timestamp)}] Fill: {log.fill_percentage != null ? log.fill_percentage.toFixed(1) : 'N/A'}% | Battery:{' '}
                                                 {log.battery}V
                                                 {typeof log.uptime_ms === 'number' && (
                                                     <> | Last cycle uptime: {formatUptimeMs(log.uptime_ms)}</>
                                                 )}
                                             </div>
                                         ))}
                                     </div>
                                )
                            ) : (
                                <div className="no-selection">
                                    Select a sensor from the left panel or network map to view data
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>

            {/* Right Sidebar */}
            <aside className="right-sidebar">
                {/* Top: Visual Map */}
                <div className="map-section">
                    <h3>Network Topology</h3>
                    <div className="map-container">
                        {nodes.length === 0 ? (
                            <div className="map-placeholder">
                                <div className="no-nodes">No network detected</div>
                            </div>
                        ) : (
                            <svg className="network-map" viewBox="0 0 400 300">
                                {/* Find HEAD node */}
                                {(() => {
                                    const head = nodes.find(n => n.role === 'HEAD')
                                    const workers = nodes.filter(n => n.role === 'WORKER')

                                    if (!head) return null

                                    // HEAD position (center top)
                                    const headX = 200
                                    const headY = 80

                                    // WORKER positions (spread below)
                                    const workerPositions = workers.map((_, idx) => {
                                        const totalWorkers = workers.length
                                        const spacing = 300 / (totalWorkers + 1)
                                        return {
                                            x: spacing * (idx + 1) + 50,
                                            y: 220
                                        }
                                    })

                                    return (
                                        <>
                                            {/* Draw lines from HEAD to each WORKER */}
                                            {workers.map((worker, idx) => (
                                                <line
                                                    key={`line-${worker.chipId}`}
                                                    x1={headX}
                                                    y1={headY}
                                                    x2={workerPositions[idx].x}
                                                    y2={workerPositions[idx].y}
                                                    stroke="#58a6ff"
                                                    strokeWidth="2"
                                                    strokeDasharray="5,5"
                                                    opacity="0.4"
                                                />
                                            ))}

                                            {/* Draw WORKER nodes */}
                                            {workers.map((worker, idx) => (
                                                <g
                                                    key={worker.chipId}
                                                    className={`map-node-svg worker ${selectedNode?.chipId === worker.chipId ? 'selected' : ''}`}
                                                    onClick={() => handleMapNodeClick(worker.chipId)}
                                                    style={{ cursor: 'pointer' }}
                                                >
                                                    <circle
                                                        cx={workerPositions[idx].x}
                                                        cy={workerPositions[idx].y}
                                                        r="30"
                                                        fill="url(#workerGradient)"
                                                        stroke="#58a6ff"
                                                        strokeWidth={selectedNode?.chipId === worker.chipId ? "4" : "2"}
                                                    />
                                                    <text
                                                        x={workerPositions[idx].x}
                                                        y={workerPositions[idx].y}
                                                        textAnchor="middle"
                                                        dominantBaseline="middle"
                                                        fill="white"
                                                        fontSize="12"
                                                        fontWeight="bold"
                                                    >
                                                        W{idx + 1}
                                                    </text>
                                                    <text
                                                        x={workerPositions[idx].x}
                                                        y={workerPositions[idx].y + 45}
                                                        textAnchor="middle"
                                                        fill="#8899a6"
                                                        fontSize="10"
                                                    >
                                                        {worker.name || worker.chipId.slice(-5)}
                                                    </text>
                                                </g>
                                            ))}

                                            {/* Draw HEAD node (on top) */}
                                            <g
                                                className={`map-node-svg head ${selectedNode?.chipId === head.chipId ? 'selected' : ''}`}
                                                onClick={() => handleMapNodeClick(head.chipId)}
                                                style={{ cursor: 'pointer' }}
                                            >
                                                <circle
                                                    cx={headX}
                                                    cy={headY}
                                                    r="35"
                                                    fill="url(#headGradient)"
                                                    stroke="#79c0ff"
                                                    strokeWidth={selectedNode?.chipId === head.chipId ? "4" : "3"}
                                                />
                                                <text
                                                    x={headX}
                                                    y={headY}
                                                    textAnchor="middle"
                                                    dominantBaseline="middle"
                                                    fill="white"
                                                    fontSize="14"
                                                    fontWeight="bold"
                                                >
                                                    HEAD
                                                </text>
                                                <text
                                                    x={headX}
                                                    y={headY + 50}
                                                    textAnchor="middle"
                                                    fill="#8899a6"
                                                    fontSize="10"
                                                >
                                                    {head.name || head.chipId.slice(-5)}
                                                </text>
                                            </g>

                                            {/* Define gradients */}
                                            <defs>
                                                <linearGradient id="headGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                                    <stop offset="0%" stopColor="#58a6ff" />
                                                    <stop offset="100%" stopColor="#1f6feb" />
                                                </linearGradient>
                                                <linearGradient id="workerGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                                    <stop offset="0%" stopColor="#388bfd" />
                                                    <stop offset="100%" stopColor="#1f6feb" />
                                                </linearGradient>
                                            </defs>
                                        </>
                                    )
                                })()}
                            </svg>
                        )}
                    </div>
                </div>

                {/* Bottom: System Stats */}
                <div className="stats-section">
                    <h3>System Overview</h3>
                    <div className="stat-grid">
                        <div className="stat-item">
                            <div className="stat-label">Total Nodes</div>
                            <div className="stat-value">{totalNodes}</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-label">Online</div>
                            <div className="stat-value">{onlineNodes}</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-label">Current Head</div>
                            <div className="stat-value">{headNode ? headNode.name || headNode.chipId.slice(-5) : 'N/A'}</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-label">Avg Battery</div>
                            <div className="stat-value">{avgBattery}V</div>
                        </div>
                        <div className={`stat-item ${systemStatus === 'offline' ? 'stat-item-offline' : ''}`}>
                            <div className="stat-label">System Uptime</div>
                            <div className={`stat-value ${systemStatus === 'offline' ? 'stat-value-offline' : ''}`}>
                                {systemUptime}
                            </div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-label">Avg Cycle Uptime</div>
                            <div className="stat-value">
                                {avgCycleUptimeMs != null ? formatUptimeMs(avgCycleUptimeMs) : 'N/A'}
                            </div>
                        </div>
                    </div>
                </div>
            </aside>
        </div>
    )
}

export default App
