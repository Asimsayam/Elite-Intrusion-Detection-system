from flask import Flask, jsonify
import pandas as pd
import os
app = Flask(__name__)
html_code = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ASIM ELITE IDS | COMMAND CENTER</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root { 
            --neon-blue: #00f2ff; 
            --neon-red: #ff003c; 
            --bg-dark: #080b10; 
            --card-bg: #111821; 
        }
        body { 
            background-color: var(--bg-dark); 
            color: white; 
            font-family: 'Segoe UI', sans-serif; 
            margin: 0; 
            padding: 20px; 
        }
        body::before { 
            content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
            background: linear-gradient(rgba(0, 242, 255, 0.03) 1px, transparent 1px), 
                        linear-gradient(90deg, rgba(0, 242, 255, 0.03) 1px, transparent 1px); 
            background-size: 40px 40px; z-index: -1; 
        }
        .header { 
            text-align: center; border-bottom: 2px solid var(--neon-blue); 
            padding-bottom: 10px; margin-bottom: 25px; 
        }
        .container { 
            display: grid; grid-template-columns: 2fr 1fr; gap: 20px; 
            max-width: 1400px; margin: auto; 
        }
        .card { 
            background: var(--card-bg); border: 1px solid #222; 
            border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.6); 
        }
        .alert-mode { 
            border: 1px solid var(--neon-red) !important; 
            box-shadow: 0 0 20px rgba(255, 0, 60, 0.4) !important; 
            animation: pulse 1.5s infinite; 
        }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
        .big-val { font-size: 2.8rem; color: var(--neon-blue); font-weight: bold; margin: 10px 0; letter-spacing: 2px; }
        .log-box { 
            background: #000; color: #0f0; height: 180px; overflow-y: auto; 
            font-family: 'Courier New', monospace; font-size: 13px; padding: 15px; 
            border-radius: 8px; border: 1px solid #333; margin-top: 15px;
        }
        canvas { max-height: 280px !important; margin-top: 15px; }
        .stat-label { color: #888; text-transform: uppercase; font-size: 12px; letter-spacing: 1px; }
        .counter-grid { display: grid; grid-template-columns: 1fr; gap: 15px; }
    </style>
</head>
<body>

<div class="header">
    <h1 style="text-shadow: 0 0 15px var(--neon-blue); margin:0;">🛡️ ASIM ELITE IDS: SOC COMMAND</h1>
    <p id="clock" style="color:var(--neon-blue); font-family:monospace;">INITIALIZING SYSTEM...</p>
</div>

<div class="container">
    <div class="card" id="main-display">
        <span class="stat-label">Live Threat Intelligence</span>
        <div id="attack-title" class="big-val">MONITORING...</div>
        <div style="height: 12px; background: #222; border-radius: 6px; overflow: hidden; margin-bottom: 10px;">
            <div id="conf-progress" style="height: 100%; width: 0%; background: var(--neon-blue); transition: 1s;"></div>
        </div>
        <div style="display:flex; justify-content: space-between;">
            <span>Confidence: <b id="conf-num" style="color:var(--neon-blue)">0</b>%</span>
            <span>Status: <b id="status-txt" style="color:#0f0">SECURE</b></span>
        </div>
        
        <canvas id="threatChart"></canvas>
    </div>

    <div class="counter-grid">
        <div class="card">
            <span class="stat-label">Total Traffic Volume</span>
            <h2 id="pkt-count" style="color:var(--neon-blue); font-size: 2.5rem; margin:10px 0;">0</h2>
            <p style="margin:0; font-size:14px; color:#aaa;">Packets Analyzed (All-Time)</p>
        </div>

        <div class="card">
            <span class="stat-label">Security Events</span>
            <h2 id="event-count" style="color:#ffcc00; font-size: 2.5rem; margin:10px 0;">0</h2>
            <p style="margin:0; font-size:14px; color:#aaa;">Unique Inspection Actions</p>
        </div>
        
        <div class="card">
            <span class="stat-label">System MetaData</span>
            <div style="margin-top:15px; font-size: 14px;">
                <p><b>Target:</b> <span style="color:var(--neon-blue)">IDS_ENGINE_v7.0</span></p>
                <p><b>Last Sync:</b> <span id="sync-time" style="color:var(--neon-blue)">--:--:--</span></p>
                <p><b>Backend:</b> FAST-API Active</p>
            </div>
        </div>
    </div>

    <div class="card" style="grid-column: span 2;">
        <span class="stat-label">Real-Time Event Logs</span>
        <div class="log-box" id="terminal-logs">
            [SYSTEM] AI Intrusion Detection System Started...<br>
            [SYSTEM] Monitoring live.csv for updates...
        </div>
    </div>
</div>

<script>
    setInterval(() => {
        document.getElementById('clock').innerText = "SYSTEM TIME: " + new Date().toLocaleTimeString();
    }, 1000);

    const ctx = document.getElementById('threatChart').getContext('2d');
    const threatChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Signature Attack', 'Anomaly (DL)', 'DDoS Flood', 'Heuristic', 'Malware'],
            datasets: [{
                label: 'Confidence (%)',
                data: [0, 0, 0, 0, 0],
                backgroundColor: 'rgba(0, 242, 255, 0.4)',
                borderColor: '#00f2ff',
                borderWidth: 2,
                borderRadius: 5
            }]
        },
        options: {
            scales: {
                y: { beginAtZero: true, max: 100, grid: { color: '#222' }, ticks: { color: '#888' } },
                x: { grid: { display: false }, ticks: { color: '#fff' } }
            },
            plugins: { legend: { display: false } }
        }
    });

    let lastTimestamp = "";

    async function pullData() {
        try {
            const res = await fetch('/get_stats');
            const data = await res.json();

            if (data.timestamp && data.timestamp !== lastTimestamp) {
                lastTimestamp = data.timestamp;

                // Update Counters from live.csv
                document.getElementById('pkt-count').innerText = data.packet_count.toLocaleString();
                document.getElementById('event-count').innerText = data.event_count.toLocaleString();
                
                // Update Main Display
                document.getElementById('attack-title').innerText = data.attack_type.toUpperCase();
                document.getElementById('conf-num').innerText = data.confidence;
                document.getElementById('conf-progress').style.width = data.confidence + "%";
                document.getElementById('sync-time').innerText = data.timestamp;

                const display = document.getElementById('main-display');
                const logWindow = document.getElementById('terminal-logs');
                const statusTxt = document.getElementById('status-txt');

                if (data.status === "ALERT" || data.status === "BATCH") {
                    display.classList.add('alert-mode');
                    statusTxt.innerText = "THREAT DETECTED";
                    statusTxt.style.color = "#ff003c";
                    
                    logWindow.innerHTML += `<br><span style="color:#ff003c">[${data.timestamp}] ALERT: ${data.attack_type} detected | Volume: ${data.packet_count}</span>`;
                    
                    // Logic to show bar on chart
                    let values = [0, 0, 0, 0, 0];
                    if(data.attack_type.includes('BENIGN')) values = [0,0,0,0,0];
                    else values[2] = data.confidence; // Default to 3rd bar for visual impact

                    threatChart.data.datasets[0].data = values;
                    threatChart.data.datasets[0].backgroundColor = 'rgba(255, 0, 60, 0.5)';
                    threatChart.data.datasets[0].borderColor = '#ff003c';
                    threatChart.update();
                } else {
                    display.classList.remove('alert-mode');
                    statusTxt.innerText = "SECURE";
                    statusTxt.style.color = "#0f0";
                    
                    threatChart.data.datasets[0].data = [0, 0, 0, 0, 0];
                    threatChart.data.datasets[0].backgroundColor = 'rgba(0, 242, 255, 0.4)';
                    threatChart.data.datasets[0].borderColor = '#00f2ff';
                    threatChart.update();
                }
                logWindow.scrollTop = logWindow.scrollHeight;
            }
        } catch (err) { console.log("Waiting for backend..."); }
    }

    setInterval(pullData, 1000); // 1 second sync
</script>

</body>
</html>
"""
@app.route('/')
def index():
    return html_code
@app.route('/get_stats')
def get_stats():
    if os.path.exists('live.csv'):
        try:
            df = pd.read_csv('live.csv')
            if not df.empty:
                
                return jsonify(df.iloc[-1].to_dict())
        except:
            pass
    return jsonify({"msg": "Syncing..."})
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
# cd /d D:\python\Elite ids

# set FLASK_APP=dashboard.py
# python -m flask run --port=5000
