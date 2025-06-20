import streamlit as st
import pandas as pd
from datetime import datetime, time
import os
import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import custom modules
from connectors.google_sheets import GoogleSheetsConnector
from analysis.analyzer import DataAnalyzer
from analysis.ai_analyzer import AIAnalyzer
from visualization.chart_generator import ChartGenerator
from reporting.report_generator import ReportGenerator
from scheduler.job_scheduler import JobScheduler
from utils.email_sender import EmailSender

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Data Analysis & Reporting Hub",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'google_connector' not in st.session_state:
    st.session_state.google_connector = None
if 'scheduler' not in st.session_state:
    st.session_state.scheduler = JobScheduler()

# Title
st.title("📊 Automated Data Analysis & Reporting Hub")
st.markdown("Connect Google Sheets → Analyze with AI → Send Reports in Multiple Languages")

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ System Status")
    if os.getenv('RESEND_API_KEY'):
        st.success("✅ Email API Ready")
    else:
        st.error("❌ Email API Missing")
    
    if os.getenv('GEMINI_API_KEY'):
        st.success("✅ AI API Ready")
    else:
        st.error("❌ AI API Missing")

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Connect & Analyze", "📧 Send Report", "⏰ Schedule Reports", "📋 Jobs"])

# Tab 1: Connect & Analyze
with tab1:
    st.header("Connect Google Sheets")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 🔐 Step 1: Upload Credentials")
        
        uploaded_file = st.file_uploader(
            "Upload Google Service Account JSON",
            type=['json'],
            help="Upload your service account key file"
        )
        
        if uploaded_file:
            try:
                creds = json.load(uploaded_file)
                
                # Validate credentials
                if 'client_email' in creds and 'private_key' in creds:
                    st.success(f"✅ Credentials loaded!")
                    st.info(f"Service Account: `{creds['client_email']}`")
                    
                    # Initialize connector
                    st.session_state.google_connector = GoogleSheetsConnector(creds)
                    st.session_state.creds = creds
                else:
                    st.error("❌ Invalid credentials file")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col2:
        st.markdown("### 📄 Step 2: Connect Sheet")
        
        if st.session_state.google_connector:
            st.info(f"""
            ⚠️ **Important**: Share your sheet with:
            `{st.session_state.creds.get('client_email')}`
            """)
            
            sheet_url = st.text_input(
                "Google Sheet URL",
                placeholder="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
            )
            
            if st.button("🔗 Connect to Sheet", type="primary"):
                if sheet_url:
                    try:
                        with st.spinner("Connecting..."):
                            data = st.session_state.google_connector.connect(sheet_url)
                            st.session_state.data = data
                            st.session_state.sheet_url = sheet_url
                            st.success(f"✅ Connected! Loaded {len(data)} rows")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        st.error("Make sure you've shared the sheet with the service account email!")
        else:
            st.warning("⚠️ Please upload credentials first")
    
    # Data Preview & Analysis
    if st.session_state.data is not None:
        st.markdown("---")
        st.header("📊 Data Analysis")
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Rows", f"{len(st.session_state.data):,}")
        with col2:
            st.metric("Total Columns", len(st.session_state.data.columns))
        with col3:
            numeric_cols = st.session_state.data.select_dtypes(include=['number']).columns
            st.metric("Numeric Columns", len(numeric_cols))
        with col4:
            missing = st.session_state.data.isnull().sum().sum()
            st.metric("Missing Values", f"{missing:,}")
        
        # Data preview
        with st.expander("📋 Data Preview", expanded=True):
            st.dataframe(st.session_state.data.head(10))
        
        # Generate analysis
        if st.button("🤖 Generate AI Analysis", type="primary"):
            with st.spinner("Analyzing with AI..."):
                analyzer = DataAnalyzer(st.session_state.data)
                ai_analyzer = AIAnalyzer()
                
                # Get AI insights
                insights = ai_analyzer.analyze_data_comprehensive(st.session_state.data)
                
                st.markdown("### 🤖 AI Insights")
                st.markdown(insights)
                
                # Save analysis
                st.session_state.ai_insights = insights
                
        # Generate visualizations
        if st.button("📈 Generate Charts"):
            with st.spinner("Creating visualizations..."):
                chart_gen = ChartGenerator()
                charts = chart_gen.generate_all_charts(st.session_state.data)
                
                st.session_state.charts = charts
                
                for title, fig in charts[:4]:  # Show first 4 charts
                    st.pyplot(fig)

# Tab 2: Send Report
# Update the Send Report section in Tab 2
with tab2:
    st.header("📧 Send Analysis Report")
    
    if st.session_state.data is None:
        st.warning("⚠️ Please connect to data first")
    else:
        with st.form("send_report"):
            col1, col2 = st.columns(2)
            
            with col1:
                recipient = st.text_input(
                    "Recipient Email",
                    value=os.getenv("DEFAULT_RECIPIENT_EMAIL")
                )
                
                language = st.selectbox(
                    "Report Language",
                    options=["en", "es", "fr", "de", "pt", "hi", "zh", "ja"],
                    format_func=lambda x: {
                        "en": "🇬🇧 English",
                        "es": "🇪🇸 Spanish",
                        "fr": "🇫🇷 French", 
                        "de": "🇩🇪 German",
                        "pt": "🇵🇹 Portuguese",
                        "hi": "🇮🇳 Hindi",
                        "zh": "🇨🇳 Chinese",
                        "ja": "🇯🇵 Japanese"
                    }[x]
                )
            
            with col2:
                report_name = st.text_input(
                    "Report Name",
                    value=f"Analysis Report - {datetime.now().strftime('%Y-%m-%d')}"
                )
                
                include_charts = st.checkbox("Include Charts", value=True)
                include_raw_data = st.checkbox("Include Data Sample", value=True)
            
            additional_context = st.text_area(
                "Additional Context (optional)",
                placeholder="Add any specific context or requirements for the AI analysis...",
                help="This will be included in the AI analysis prompt"
            )
            
            if st.form_submit_button("📧 Send Report Now", type="primary"):
                with st.spinner(f"Generating comprehensive report in {language.upper()}..."):
                    try:
                        # Generate comprehensive analysis
                        analyzer = DataAnalyzer(st.session_state.data)
                        ai_analyzer = AIAnalyzer()
                        chart_gen = ChartGenerator()
                        
                        # Get AI insights with language support
                        with st.spinner("🤖 Generating AI analysis..."):
                            ai_insights = ai_analyzer.analyze_data_comprehensive(
                                st.session_state.data, 
                                language
                            )
                        
                        # Generate charts
                        charts = []
                        if include_charts:
                            with st.spinner("📊 Creating visualizations..."):
                                charts = chart_gen.generate_all_charts(st.session_state.data)
                        
                        # Generate report
                        with st.spinner("📄 Generating PDF report..."):
                            report_gen = ReportGenerator()
                            report_content = report_gen.generate_multilingual_report(
                                data=st.session_state.data,
                                language=language,
                                report_name=report_name,
                                include_charts=include_charts,
                                include_raw_data=include_raw_data,
                                ai_insights=ai_insights,
                                charts=charts
                            )
                        
                        # Send email
                        with st.spinner("📧 Sending email..."):
                            email_sender = EmailSender()
                            success = email_sender.send_report(
                                recipient_email=recipient,
                                report_content=report_content,
                                report_name=report_name,
                                language=language
                            )
                        
                        if success:
                            st.success(f"✅ Report sent successfully to {recipient}!")
                            st.balloons()
                            
                            # Show preview
                            with st.expander("📄 View Report Preview"):
                                st.markdown(report_content['html'], unsafe_allow_html=True)
                        else:
                            st.error("❌ Failed to send report. Please check your email configuration.")
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        logger.error(f"Report generation error: {str(e)}", exc_info=True)

# Tab 3: Schedule Reports
with tab3:
    st.header("⏰ Schedule Automated Reports")
    
    if st.session_state.data is None:
        st.warning("⚠️ Please connect to data first")
    else:
        with st.form("schedule_report"):
            col1, col2 = st.columns(2)
            
            with col1:
                job_name = st.text_input("Job Name", value="Daily Analysis Report")
                recipient = st.text_input("Recipient Email", value=os.getenv("DEFAULT_RECIPIENT_EMAIL"))
                frequency = st.selectbox("Frequency", ["Daily", "Weekly", "Hourly"])
                language = st.selectbox(
                    "Report Language",
                    options=["en", "es", "fr", "de", "pt", "hi", "zh", "ja"],
                    format_func=lambda x: {
                        "en": "English", "es": "Spanish", "fr": "French",
                        "de": "German", "pt": "Portuguese", "hi": "Hindi",
                        "zh": "Chinese", "ja": "Japanese"
                    }[x]
                )
            
            with col2:
                if frequency == "Daily":
                    run_time = st.time_input("Run Time", value=time(9, 0))
                elif frequency == "Weekly":
                    day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
                    run_time = st.time_input("Run Time", value=time(9, 0))
                
                include_charts = st.checkbox("Include Charts", value=True)
                auto_refresh = st.checkbox("Auto-refresh data", value=True, 
                                         help="Fetch latest data from Google Sheets before each report")
            
            if st.form_submit_button("📅 Schedule Report", type="primary"):
                # Prepare job config
                job_config = {
                    "job_name": job_name,
                    "recipient": recipient,
                    "language": language,
                    "include_charts": include_charts,
                    "auto_refresh": auto_refresh,
                    "sheet_url": st.session_state.sheet_url,
                    "creds": st.session_state.creds
                }
                
                schedule_params = {"frequency": frequency.lower()}
                if frequency == "Daily":
                    schedule_params["hour"] = run_time.hour
                    schedule_params["minute"] = run_time.minute
                elif frequency == "Weekly":
                    schedule_params["day"] = day.lower()[:3]
                    schedule_params["hour"] = run_time.hour
                    schedule_params["minute"] = run_time.minute
                
                # Schedule job
                job_id = st.session_state.scheduler.schedule_job(
                    job_config=job_config,
                    schedule_params=schedule_params,
                    initial_data=st.session_state.data
                )
                
                if job_id:
                    st.success(f"✅ Report scheduled! Job ID: {job_id}")
                else:
                    st.error("Failed to schedule report")

# Tab 4: Job Management
with tab4:
    st.header("📋 Scheduled Jobs")
    
    jobs = st.session_state.scheduler.get_all_jobs()
    
    if not jobs:
        st.info("No scheduled jobs yet")
    else:
        for job in jobs:
            with st.expander(f"📋 {job['config'].get('job_name', 'Unnamed Job')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Job ID:** {job['id']}")
                    st.write(f"**Recipient:** {job['config'].get('recipient')}")
                    st.write(f"**Language:** {job['config'].get('language', 'en').upper()}")
                
                with col2:
                    st.write(f"**Frequency:** {job['schedule'].get('frequency', 'Unknown')}")
                    st.write(f"**Next Run:** {job.get('next_run', 'N/A')}")
                
                with col3:
                    if st.button(f"▶️ Run Now", key=f"run_{job['id']}"):
                        st.session_state.scheduler.run_job_now(job['id'])
                        st.success("Job triggered!")
                    
                    if st.button(f"🗑️ Delete", key=f"del_{job['id']}"):
                        st.session_state.scheduler.delete_job(job['id'])
                        st.rerun()