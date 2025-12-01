import os
import json
# Import 'request' to handle form submissions
from flask import Flask, render_template, request
from google import genai
from google.genai import types

app = Flask(__name__)

# --- CONFIGURATION (Load API Key) ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# --- Helper Functions ---
def load_default_config(filename="mock_kernel_module.conf"):
    try:
        with open(filename, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: Configuration file '{filename}' not found."

def analyze_security_with_gemini(config_text):
    if not GEMINI_API_KEY:
        return {"error": "GEMINI_API_KEY not configured. Cannot perform analysis."}
    
    if not config_text or config_text.strip() == "":
        return {"error": "No configuration provided for analysis."}
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Define the STRUCTURED OUTPUT we want (JSON Schema)
        schema = types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "config_setting": types.Schema(type=types.Type.STRING, description="The specific CONFIG_ variable."),
                    "severity": types.Schema(type=types.Type.STRING, description="CRITICAL, HIGH, MEDIUM, or LOW."),
                    "issue_summary": types.Schema(type=types.Type.STRING, description="Why this setting is a security risk."),
                    "remediation_action": types.Schema(type=types.Type.STRING, description="Specific action to take to harden the setting (e.g., Change to 'n')."),
                    "feynman_explanation": types.Schema(type=types.Type.STRING, description="A simple, non-technical explanation of the risk for a beginner.")
                },
                required=["config_setting", "severity", "issue_summary", "remediation_action", "feynman_explanation"]
            )
        )

        prompt = (
            f"As an elite DevSecOps expert, audit the following Linux kernel configuration for security vulnerabilities and hardening needs. "
            f"Focus specifically on settings that reduce auditability or increase attack surface. "
            f"For each finding, provide a simple 'Feynman' explanation of the risk. "
            f"The configuration is: \n\n{config_text}"
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )

        return json.loads(response.text)

    except Exception as e:
        return {"error": f"Gemini API Error: {str(e)}"}

# --- Flask Route (Now handles both GET and POST) ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # User submitted a new config via the form
        kernel_config_text = request.form.get('kernel_config', load_default_config())
        status = "AI Analysis Running..."
    else:
        # Initial load (GET) - use the default config
        kernel_config_text = load_default_config()
        status = "AI Analysis Complete! (Default Config)"
        
    
    # Analyze the config using Gemini
    security_findings = analyze_security_with_gemini(kernel_config_text)
    
    if "error" in security_findings:
        findings_html = f"<p style='color: red;'>ERROR: {security_findings['error']}</p>"
        status = "Gemini Error - Check API Key & Logs"
    else:
        # Format the structured JSON output into HTML for display
        findings_html = format_findings_to_html(security_findings)
        
        # Only set status to 'Complete' if analysis ran successfully (after POST or on GET)
        if request.method == 'POST' or status != "Gemini Error - Check API Key & Logs":
            status = "AI Analysis Complete!"
        
    return render_template('index.html', 
                           status=status,
                           config_content=kernel_config_text,
                           findings_html=findings_html)

# --- Output Formatting ---
def format_findings_to_html(findings):
    html = ""
    if not findings:
        return "<p>No critical security issues found.</p>"

    for finding in findings:
        color = "red" if finding.get("severity", "").upper() == "CRITICAL" else "orange" if finding.get("severity", "").upper() == "HIGH" else "green"
        
        html += f"""
        <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 15px;">
            <p><strong>🚨 {finding.get('severity', 'UNKNOWN')} Issue:</strong> {finding.get('issue_summary', '')} </p>
            <p><strong>Config:</strong> <code>{finding.get('config_setting', '')}</code></p>
            <p style='color: {color};'><strong>🛠 Remediation:</strong> {finding.get('remediation_action', '')}</p>
            <p><strong>🧠 Feynman Explanation:</strong> {finding.get('feynman_explanation', '')}</p>
        </div>
        """
    return html

if __name__ == '__main__':
    app.run(debug=True)


