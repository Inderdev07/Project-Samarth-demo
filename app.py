from flask import Flask, request, jsonify
import json

app = Flask(__name__)

# --- Sample in-memory datasets (for quick demo) ---
rainfall_data = {
    "Punjab": [810, 760, 790],
    "Haryana": [620, 580, 600],
    "Maharashtra": [890, 910, 870]
}

crops_data = {
    "Punjab": {"Wheat": 16000, "Rice": 14000},
    "Haryana": {"Wheat": 12000, "Rice": 8000},
    "Maharashtra": {"Sugarcane": 22000, "Cotton": 11000}
}

# Helper for top M crops
def top_crops_in_state(state, m=3):
    crops = crops_data.get(state, {})
    sorted_crops = sorted(crops.items(), key=lambda x: x[1], reverse=True)
    return sorted_crops[:m]

@app.route('/')
def home():
    # Single-file page with inline CSS + JS (Chart.js via CDN)
    return '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Project Samarth — Demo</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root{
      --bg:#0f1724; --card:#0b1220; --accent:#7c3aed; --muted:#9ca3af; --glass:rgba(255,255,255,0.03);
    }
    *{box-sizing:border-box}
    body{
      margin:0;
      font-family:Inter,system-ui,-apple-system,"Segoe UI",Roboto, "Helvetica Neue",Arial;
      background: linear-gradient(180deg,#061021 0%, #07142a 100%);
      color:#edf2f7;
      display:flex;align-items:center;justify-content:center;height:100vh;
    }
    .container{
      width:920px; max-width:96%; background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
      border-radius:12px; padding:18px; box-shadow: 0 10px 30px rgba(2,6,23,0.6);
      display:grid; grid-template-columns: 360px 1fr; gap:16px; align-items:start;
    }
    .left{
      background:var(--card); padding:14px; border-radius:10px; min-height:360px;
    }
    h1{font-size:18px;margin:0 0 8px 0}
    p.lead{margin:0 0 12px 0;color:var(--muted); font-size:13px}
    .input-row{display:flex;gap:8px;margin-bottom:10px}
    input#question{
      flex:1;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.04);
      background:var(--glass); color:inherit; outline:none;
    }
    button#ask{
      padding:10px 12px;border-radius:8px;background:linear-gradient(180deg,var(--accent),#5b21b6);
      border:none;color:white;font-weight:600;cursor:pointer;
    }
    button#ask:disabled{opacity:0.6;cursor:default}
    .suggestions{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}
    .chip{background:rgba(255,255,255,0.03);padding:6px 9px;border-radius:999px;font-size:13px;color:var(--muted);cursor:pointer;border:1px solid rgba(255,255,255,0.03)}
    .chat-box{height:180px;overflow:auto;padding:10px;border-radius:8px;background:linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.02)); border:1px solid rgba(255,255,255,0.02)}
    .msg.user{text-align:right;color:#a5b4fc;margin:8px 0}
    .msg.bot{text-align:left;color:#c7d2fe;margin:8px 0}
    .meta{font-size:12px;color:var(--muted);margin-top:8px}
    .right{
      background:var(--card); padding:14px; border-radius:10px; min-height:360px; display:flex;flex-direction:column;
    }
    .card-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
    .chart-container{flex:1;display:flex;flex-direction:column;gap:12px}
    .small{font-size:13px;color:var(--muted)}
    .hint{font-size:12px;color:#94a3b8;margin-top:6px}
  </style>
</head>
<body>
  <div class="container">
    <div class="left">
      <h1>Project Samarth — Data Q&amp;A (Demo)</h1>
      <p class="lead">Ask natural questions about rainfall and crop production. Use suggestions to get started.</p>

      <div class="suggestions" id="suggestions">
        <div class="chip" onclick="fill('Compare rainfall in Punjab and Haryana')">Compare rainfall in Punjab and Haryana</div>
        <div class="chip" onclick="fill('Top 3 crops in Punjab')">Top 3 crops in Punjab</div>
        <div class="chip" onclick="fill('Average rainfall in India')">Average rainfall in India</div>
        <div class="chip" onclick="fill('District with highest production of Wheat in Punjab')">District highest Wheat (sample)</div>
      </div>

      <div class="input-row">
        <input id="question" placeholder="Try: Compare rainfall in Punjab and Haryana (press Enter)" onkeydown="onKey(event)">
        <button id="ask" onclick="ask()" title="Ask (Enter)">Ask</button>
      </div>

      <div class="chat-box" id="chat">
        <div class="msg bot">Hi — try a question or click a suggestion above. The demo uses sample datasets.</div>
      </div>

      <div class="meta">Tip: press <strong>Enter</strong> to send. Button disables while processing.</div>
    </div>

    <div class="right">
      <div class="card-header">
        <div>
          <div style="font-weight:700">Result & Visualization</div>
          <div class="small">Chart updates for comparisons & top crops</div>
        </div>
        <div class="small">Data source: <em>Sample (demo)</em></div>
      </div>

      <div class="chart-container">
        <canvas id="mainChart" style="background:transparent;border-radius:8px"></canvas>
        <div id="raw" class="small hint">Raw facts and citations will appear here.</div>
      </div>
    </div>
  </div>

<script>
const askBtn = document.getElementById('ask');
const questionInput = document.getElementById('question');
const chat = document.getElementById('chat');
const rawDiv = document.getElementById('raw');

function fill(text){
  questionInput.value = text;
  questionInput.focus();
}

function onKey(e){
  if(e.key === 'Enter') ask();
}

async function ask(){
  const q = questionInput.value.trim();
  if(!q) return;
  // Add user message
  chat.innerHTML += `<div class="msg user">${escapeHtml(q)}</div>`;
  chat.scrollTop = chat.scrollHeight;
  askBtn.disabled = true;
  askBtn.textContent = 'Thinking...';

  try{
    const res = await fetch('/ask', {
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({question: q})
    });
    const data = await res.json();
    // Append bot message
    chat.innerHTML += `<div class="msg bot">${escapeHtml(data.text)}</div>`;
    chat.scrollTop = chat.scrollHeight;

    rawDiv.innerHTML = '';
    if(data.type === 'rainfall_compare'){
      renderBarChart(data.labels, data.values, 'Average Rainfall (mm)');
      rawDiv.innerHTML = `Compared states: ${escapeHtml(data.labels.join(', '))} · Source: IMD (sample).`;
    } else if(data.type === 'top_crops'){
      renderBarChart(data.labels, data.values, 'Production (tonnes)');
      rawDiv.innerHTML = `Top crops in ${escapeHtml(data.state)} · Source: Agriculture Ministry (sample).`;
    } else {
      // clear chart
      renderBarChart([], [], '');
      rawDiv.innerHTML = data.citation ? `Citation: ${escapeHtml(data.citation)}` : 'No structured data to show.';
    }

  }catch(err){
    chat.innerHTML += `<div class="msg bot">Error: could not reach server.</div>`;
  } finally {
    askBtn.disabled = false;
    askBtn.textContent = 'Ask';
    questionInput.value = '';
  }
}

function escapeHtml(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

/* Chart.js */
let chart = null;
function renderBarChart(labels, values, label){
  const ctx = document.getElementById('mainChart').getContext('2d');
  if(chart) chart.destroy();
  chart = new Chart(ctx, {
    type:'bar',
    data:{ labels: labels, datasets: [{ label: label, data: values, borderRadius:6 }] },
    options:{
      responsive:true,
      scales:{ x: { ticks: {color:'#cbd5e1'} }, y: { ticks: {color:'#cbd5e1'} } },
      plugins:{ legend: { display:false } }
    }
  });
}
</script>
</body>
</html>
'''

@app.route('/ask', methods=['POST'])
def ask():
    payload = request.get_json() or {}
    q = payload.get('question', '').lower()

    # Compare Punjab & Haryana rainfall
    if "compare" in q and "punjab" in q and "haryana" in q:
        p = sum(rainfall_data["Punjab"]) / len(rainfall_data["Punjab"])
        h = sum(rainfall_data["Haryana"]) / len(rainfall_data["Haryana"])
        text = f"Average rainfall — Punjab: {p:.2f} mm, Haryana: {h:.2f} mm (sample IMD data)."
        return jsonify({
            "type":"rainfall_compare",
            "text": text,
            "labels":["Punjab","Haryana"],
            "values":[round(p,2), round(h,2)],
            "citation":"IMD (sample) - demo dataset"
        })

    # Average rainfall overall
    if "average" in q and "rainfall" in q:
        all_vals = [v for lst in rainfall_data.values() for v in lst]
        avg = sum(all_vals)/len(all_vals)
        return jsonify({
            "type":"info",
            "text": f"India's demo average rainfall across states: {avg:.2f} mm.",
            "citation":"IMD (sample) - demo dataset"
        })

    # Top crops in a given state (try: Top 3 crops in Punjab)
    if ("top" in q or "most produced" in q) and any(s.lower() in q for s in crops_data.keys()):
        state = next(s for s in crops_data.keys() if s.lower() in q)
        top = top_crops_in_state(state, m=3)
        labels = [c for c,_ in top]
        values = [v for _,v in top]
        text = f"Top crops in {state}: " + ", ".join([f"{c} ({v} t)" for c,v in top])
        return jsonify({
            "type":"top_crops",
            "text": text,
            "state": state,
            "labels": labels,
            "values": values,
            "citation":"Min. of Agriculture (sample) - demo dataset"
        })

    # Fallback
    suggestions = [
        "Compare rainfall in Punjab and Haryana",
        "Top 3 crops in Punjab",
        "Average rainfall in India",
        "Most produced crop in India"
    ]
    return jsonify({
        "type":"fallback",
        "text":"I didn't understand that fully. Try one of these examples shown in the left panel.",
        "suggestions": suggestions
    })

if __name__ == '__main__':
    app.run(debug=True)
