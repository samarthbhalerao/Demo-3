import streamlit as st
import pandas as pd
import sqlite3
import random
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="The National Investor Literacy & Governance Trust",
    page_icon="🏛️",
    layout="wide"
)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("investor_trust.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            score INTEGER,
            reward INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS governance_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mandate_id TEXT UNIQUE,
            company TEXT,
            proposal TEXT,
            vote TEXT,
            reward INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# --- INITIALIZE ONBOARDING SESSION STATE ---
if "onboarding_step" not in st.session_state:
    st.session_state["onboarding_step"] = 1

# Pre-populate state for Demo Data Autofill feature
if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""
if "user_pan" not in st.session_state:
    st.session_state["user_pan"] = ""
if "user_mobile" not in st.session_state:
    st.session_state["user_mobile"] = ""
if "user_demat" not in st.session_state:
    st.session_state["user_demat"] = ""
if "user_upi" not in st.session_state:
    st.session_state["user_upi"] = ""

# --- AUTOFILL HELPER FUNCTION ---
def autofill_demo_credentials():
    st.session_state["user_name"] = "Samarth Sharad Bhalerao"
    st.session_state["user_pan"] = "ABCPS1234F"
    st.session_state["user_mobile"] = "9876543210"
    st.session_state["user_demat"] = "1208160009482156"

def autofill_demo_payout():
    st.session_state["user_upi"] = "samarth.bhalerao@upi"

# --- HELPER FUNCTIONS FOR DB ---
def get_user_stats():
    conn = sqlite3.connect("investor_trust.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT score, reward FROM quiz_history")
    quiz_rows = cursor.fetchall()
    quiz_rewards = sum(r[1] for r in quiz_rows) if quiz_rows else 0
    quiz_points = sum(r[0] * 10 for r in quiz_rows) if quiz_rows else 0
    
    cursor.execute("SELECT COUNT(*), SUM(reward) FROM governance_votes")
    vote_data = cursor.fetchone()
    total_votes = vote_data[0] or 0
    vote_rewards = vote_data[1] or 0
    vote_points = total_votes * 10
    
    conn.close()
    
    base_escrow = 400.00
    base_points = 80
    
    total_escrow = base_escrow + quiz_rewards + vote_rewards
    total_points = base_points + quiz_points + vote_points
    
    return total_escrow, total_points

def is_quiz_completed():
    conn = sqlite3.connect("investor_trust.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM quiz_history")
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def record_quiz(score, reward):
    conn = sqlite3.connect("investor_trust.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quiz_history (score, reward) VALUES (?, ?)", (score, reward))
    conn.commit()
    conn.close()

def get_voted_mandates():
    conn = sqlite3.connect("investor_trust.db")
    cursor = conn.cursor()
    cursor.execute("SELECT mandate_id, vote FROM governance_votes")
    rows = cursor.fetchall()
    conn.close()
    return dict(rows)

def record_vote(mandate_id, company, proposal, vote, reward):
    conn = sqlite3.connect("investor_trust.db")
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO governance_votes (mandate_id, company, proposal, vote, reward)
            VALUES (?, ?, ?, ?, ?)
        ''', (mandate_id, company, proposal, vote, reward))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

# --- MODAL FUNCTION FOR IN-APP DEPOSITORY VOTING ---
@st.dialog("🔒 Official Depository Remote e-Voting Gateway", width="large")
def render_voting_modal(mandate, selected_vote):
    evsn_code = f"24091800{random.randint(10,99)}"
    
    st.markdown(f"### **Company:** {mandate['company']}")
    st.markdown(f"**Proposal:** {mandate['proposal']}")
    st.markdown(f"**Your Decision:** :blue[**{selected_vote}**]")
    
    st.divider()
    
    st.caption("DEPOSITORY AUTHENTICATION DETAILS")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Depository Service:** NSDL / CDSL")
        st.write(f"**EVSN Event Code:** `{evsn_code}`")
    with col2:
        demat_display = st.session_state.get('user_demat', '1208160009482156')
        st.write(f"**DP ID / Client ID:** `{demat_display[:8]}XXXXXX`")
        st.write(f"**Demat Holder:** {st.session_state.get('user_name', 'Samarth Sharad Bhalerao')}")
        
    st.info("💡 **Security Notice:** A 6-digit OTP has been dispatched to your mobile number registered with your Demat account.")
    
    otp_input = st.text_input("Enter 6-Digit Verification OTP:", placeholder="e.g. 123456", max_chars=6)
    
    col_submit, col_cancel = st.columns([1, 1])
    
    with col_submit:
        if st.button("Submit & Authorize Vote", type="primary", use_container_width=True):
            if len(otp_input) > 0:
                record_vote(mandate["id"], mandate["company"], mandate["proposal"], selected_vote, 100)
                st.balloons()
                st.success("🎉 Vote successfully recorded on depository ledger! **₹100 Escrow Reward** credited.")
                st.rerun()
            else:
                st.error("Please enter the OTP to proceed.")

# ==============================================================================
# ONBOARDING FLOW (STEPS 1 - 4)
# ==============================================================================

# --- STEP 1: SPLASH SCREEN (5 SECONDS) ---
if st.session_state["onboarding_step"] == 1:
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 3.2rem;'>🏛️</h1>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 2.8rem;'>The National Investor Literacy & Governance Trust</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: gray;'>CSR-Funded (Section 135, Schedule VII) Shareholder Platform</h4>", unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.spinner("Initializing Secure Ecosystem..."):
        time.sleep(5)
    
    st.session_state["onboarding_step"] = 2
    st.rerun()

# --- STEP 2: PRIMARY IDENTIFIER ---
elif st.session_state["onboarding_step"] == 2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.title("Step 1 of 3: Primary Identification & Demat Mapping")
    st.caption("Verify your identity to map active shareholder proxy mandates in your Demat account.")
    
    st.button("⚡ Autofill Demo Credentials", on_click=autofill_demo_credentials, type="secondary")
    
    with st.form("identity_form"):
        name = st.text_input("Full Legal Name (as per PAN):", value=st.session_state["user_name"])
        pan = st.text_input("PAN (Permanent Account Number):", value=st.session_state["user_pan"], max_chars=10)
        mobile = st.text_input("Mobile Number (Linked with Demat):", value=st.session_state["user_mobile"], max_chars=10)
        demat = st.text_input("16-Digit Demat Account ID (BO ID / Client ID):", value=st.session_state["user_demat"], max_chars=16)
        
        col1, col2 = st.columns([4, 1])
        with col2:
            submitted = st.form_submit_button("Next Step ➔", type="primary", use_container_width=True)
            
        if submitted:
            if name and pan and mobile and demat:
                st.session_state["user_name"] = name
                st.session_state["user_pan"] = pan
                st.session_state["user_mobile"] = mobile
                st.session_state["user_demat"] = demat
                st.session_state["onboarding_step"] = 3
                st.rerun()
            else:
                st.error("Please fill in all identification details or click 'Autofill Demo Credentials'.")

# --- STEP 3: CONSENT & DPDP ACT COMPLIANCE ---
elif st.session_state["onboarding_step"] == 3:
    st.markdown("<br>", unsafe_allow_html=True)
    st.title("Step 2 of 3: User Consent & Privacy Policy")
    st.caption("Compliance with the Digital Personal Data Protection (DPDP) Act, 2023 & SEBI Regulations.")
    
    st.markdown("""
    > **Legal Mandate & Authorization Terms:**
    > 
    > 1. **Data Utilization:** You explicitly authorize *The National Investor Literacy & Governance Trust* to verify corporate meeting notifications and EVSN events against your Demat account (`{}` / `{}`).
    > 2. **Voting Execution:** Remote e-Voting will be executed exclusively by user authorization via official Depository Multi-Factor Authentication (OTP).
    > 3. **Educational Escrow Payouts:** Funds accrued from governance engagement and quizzes are disbursed via verified banking channels in accordance with Section 194R/194B of the Income Tax Act.
    """.format(st.session_state.get('user_pan', 'PAN'), st.session_state.get('user_demat', 'DEMAT')))
    
    st.divider()
    
    consent_given = st.checkbox("I have read, understood, and MANDATORILY AGREE to the processing of my investor data for governance proxy participation.", value=False)
    
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("Proceed to Payout ➔", type="primary", use_container_width=True):
            if consent_given:
                st.session_state["onboarding_step"] = 4
                st.rerun()
            else:
                st.error("You must accept the mandatory consent terms to proceed.")

# --- STEP 4: PAYOUT CHANNEL VERIFICATION ---
elif st.session_state["onboarding_step"] == 4:
    st.markdown("<br>", unsafe_allow_html=True)
    st.title("Step 3 of 3: Escrow Payout Channel Setup")
    st.caption("Link your UPI VPA to instantly receive your ₹100 participation rewards and quiz earnings.")
    
    st.button("⚡ Autofill Demo Payout VPA", on_click=autofill_demo_payout, type="secondary")
    
    with st.form("payout_form"):
        upi_id = st.text_input("Enter UPI ID (VPA):", value=st.session_state["user_upi"], placeholder="e.g. mobile@upi")
        
        col1, col2 = st.columns([4, 1])
        with col2:
            finish = st.form_submit_button("Complete Setup & Launch 🚀", type="primary", use_container_width=True)
            
        if finish:
            if upi_id:
                st.session_state["user_upi"] = upi_id
                st.session_state["onboarding_step"] = 5  # Launch main app
                st.rerun()
            else:
                st.error("Please provide a valid UPI ID to receive escrow rewards.")

# ==============================================================================
# MAIN APP DASHBOARD (STEP 5)
# ==============================================================================
elif st.session_state["onboarding_step"] == 5:
    
    st.title("🏛️ The National Investor Literacy & Governance Trust")
    st.caption(f"Logged in as: **{st.session_state.get('user_name', 'Samarth Sharad Bhalerao')}** | PAN: `{st.session_state.get('user_pan', 'ABCPS1234F')}` | UPI: `{st.session_state.get('user_upi', 'samarth.bhalerao@upi')}`")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- DASHBOARD METRICS ---
    escrow_balance, governance_score = get_user_stats()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Escrow Balance", f"₹{escrow_balance:.2f}")
    with col2:
        st.metric("Governance Score", f"{governance_score} pts")
    with col3:
        tier = "Alpha Steward" if governance_score >= 100 else "Beta Steward"
        st.metric("Current Status Tier", tier)
    with col4:
        pts_to_next = max(0, 150 - governance_score)
        st.metric("Points to Alpha Steward", f"{pts_to_next} pts")

    st.divider()

    # --- TABS NAVIGATION ---
    tab1, tab2, tab3, tab4 = st.tabs([
        " Daily Byte Quiz", 
        " Active Governance Votes", 
        " Tier Matrix", 
        " Ledger"
    ])

    # --- TAB 1: DAILY BYTE QUIZ ---
    with tab1:
        st.header("Daily Byte Quiz")
        st.write("Test your knowledge on corporate governance, ESG practices, and CSR mandates to earn Escrow rewards!")
        
        if is_quiz_completed():
            st.success(" You have completed today's quiz and claimed your reward!")
            
            if "quiz_analysis" in st.session_state:
                st.subheader("📊 Answer Breakdown & Explanation")
                for idx, item in enumerate(st.session_state["quiz_analysis"], start=1):
                    status_icon = "✅" if item["is_correct"] else "❌"
                    with st.expander(f"{status_icon} Question {idx}: {item['question']}", expanded=True):
                        st.write(f"**Your Answer:** {item['user_answer']}")
                        st.write(f"**Correct Answer:** {item['correct_answer']}")
                        st.info(f"💡 **Explanation:** {item['explanation']}")
        else:
            with st.form("quiz_form"):
                q1 = st.radio(
                    "1. What is the most effective corporate mechanism to reduce greenwashing risk?",
                    [
                        "A. Increasing marketing spend on sustainability campaigns",
                        "B. Mandating third-party ESG audits & transparent reporting metrics",
                        "C. Publishing annual pledges without verifiable targets",
                        "D. Changing corporate branding to green colors"
                    ]
                )
                
                q2 = st.radio(
                    "2. Under Indian Companies Act, Section 135, what percentage of average net profits must eligible companies spend on CSR?",
                    ["A. 1%", "B. 2%", "C. 5%", "D. 10%"]
                )
                
                q3 = st.radio(
                    "3. What constitutes a 'Related Party Transaction' requiring audit committee approval?",
                    [
                        "A. Transactions with external retail customers",
                        "B. Business deals between a company and its directors/subsidiaries",
                        "C. Open market stock purchases",
                        "D. Regular employee salary payments"
                    ]
                )
                
                q4 = st.radio(
                    "4. Which Schedule of the Companies Act, 2013 outlines permitted CSR activities?",
                    ["A. Schedule V", "B. Schedule VI", "C. Schedule VII", "D. Schedule XI"]
                )
                
                q5 = st.radio(
                    "5. What is the primary purpose of a Whistleblower Policy in corporate governance?",
                    [
                        "A. To penalize low-performing employees",
                        "B. To provide a secure channel for reporting illegal or unethical practices",
                        "C. To manage public relations during a crisis",
                        "D. To handle customer returns and refunds"
                    ]
                )
                
                q6 = st.radio(
                    "6. Independent directors are expected to serve a maximum of how many consecutive terms?",
                    ["A. 1 term", "B. 2 terms", "C. 3 terms", "D. Unlimited terms"]
                )
                
                submitted = st.form_submit_button("Submit Quiz")
                
                if submitted:
                    questions_data = [
                        {
                            "question": "What is the most effective corporate mechanism to reduce greenwashing risk?",
                            "user_answer": q1,
                            "correct_answer": "B. Mandating third-party ESG audits & transparent reporting metrics",
                            "is_correct": "B. Mandating third-party ESG audits" in q1,
                            "explanation": "Independent audits ensure ESG claims are backed by verifiable data rather than superficial marketing."
                        },
                        {
                            "question": "Under Indian Companies Act, Section 135, what percentage of average net profits must eligible companies spend on CSR?",
                            "user_answer": q2,
                            "correct_answer": "B. 2%",
                            "is_correct": "B. 2%" in q2,
                            "explanation": "Section 135 mandates that companies meeting threshold criteria spend at least 2% of average net profits made during the 3 immediately preceding financial years."
                        },
                        {
                            "question": "What constitutes a 'Related Party Transaction' requiring audit committee approval?",
                            "user_answer": q3,
                            "correct_answer": "B. Business deals between a company and its directors/subsidiaries",
                            "is_correct": "B. Business deals between a company" in q3,
                            "explanation": "Related Party Transactions involve contracts with directors, key managerial personnel, or related entities to prevent conflicts of interest."
                        },
                        {
                            "question": "Which Schedule of the Companies Act, 2013 outlines permitted CSR activities?",
                            "user_answer": q4,
                            "correct_answer": "C. Schedule VII",
                            "is_correct": "C. Schedule VII" in q4,
                            "explanation": "Schedule VII defines permitted activities such as eradicating hunger, promoting education, gender equality, and environmental sustainability."
                        },
                        {
                            "question": "What is the primary purpose of a Whistleblower Policy in corporate governance?",
                            "user_answer": q5,
                            "correct_answer": "B. To provide a secure channel for reporting illegal or unethical practices",
                            "is_correct": "B. To provide a secure channel" in q5,
                            "explanation": "A robust whistleblower system protects employees reporting unethical or illegal activities from retaliation."
                        },
                        {
                            "question": "Independent directors are expected to serve a maximum of how many consecutive terms?",
                            "user_answer": q6,
                            "correct_answer": "B. 2 terms",
                            "is_correct": "B. 2 terms" in q6,
                            "explanation": "Under regulatory governance norms, an independent director can hold office for up to two consecutive terms of up to 5 years each."
                        }
                    ]
                    
                    score = sum(1 for item in questions_data if item["is_correct"])
                    reward = score * 25
                    
                    record_quiz(score, reward)
                    st.session_state["quiz_analysis"] = questions_data
                    
                    st.balloons()
                    st.success(f"Quiz Submitted! You scored {score}/6 and earned **₹{reward}.00** Escrow reward!")
                    st.rerun()

    # --- TAB 2: GOVERNANCE VOTES ---
    with tab2:
        st.header("Active Proxy Mandates")
        st.write("Exercise your voting rights on key corporate proposals. Earn ₹100 Escrow balance per vote cast.")
        
        mandates = [
            {
                "id": "MND-001",
                "company": "Zeta Tech Ltd",
                "category": "Executive Compensation Clash",
                "proposal": "Approve 35% increase in executive remuneration package.",
                "analysis": "AI Governance Analysis: The proposed 35% pay increase significantly outpaces revenue growth (8% YoY). Peer benchmarking indicates executive pay is already in the 90th percentile.",
                "recommendation": "AGAINST"
            },
            {
                "id": "MND-002",
                "company": "IndoCarbon Energy",
                "category": "Greenwashing Audit Mandate",
                "proposal": "Mandate independent third-party carbon audits for major projects.",
                "analysis": "AI Governance Analysis: IndoCarbon has faced regulatory scrutiny over scope 3 emissions reporting. Independent audits will reduce compliance risks and improve ESG rating transparency.",
                "recommendation": "FOR"
            },
            {
                "id": "MND-003",
                "company": "Apex Healthcare Solutions",
                "category": "Board Independence & Diversity",
                "proposal": "Appoint two additional independent directors with healthcare compliance expertise.",
                "analysis": "AI Governance Analysis: Currently, independent directors hold only 30% of board seats. Adding two qualified independent members aligns with regulatory best practices.",
                "recommendation": "FOR"
            },
            {
                "id": "MND-004",
                "company": "Nexus Logistics Inc.",
                "category": "CSR Fund Reallocation",
                "proposal": "Reallocate 40% of CSR funds from local education programs to corporate technology incubators.",
                "analysis": "AI Governance Analysis: Diverting CSR funds toward technology incubators borders on commercial R&D rather than genuine social impact under Schedule VII mandates.",
                "recommendation": "AGAINST"
            }
        ]
        
        voted_dict = get_voted_mandates()
        
        for m in mandates:
            with st.expander(f"📌 {m['company']} — {m['category']} ({m['id']})", expanded=True):
                st.markdown(f"**Proposal:** {m['proposal']}")
                st.info(f"💡 **Platform Analysis Summary:**\n\n{m['analysis']}\n\n*Suggested Vote:* **{m['recommendation']}**")
                
                if m["id"] in voted_dict:
                    st.success(f" You voted: **{voted_dict[m['id']]}**")
                else:
                    col_a, col_b, col_c = st.columns([1, 1, 4])
                    with col_a:
                        if st.button(f"Vote FOR", key=f"for_{m['id']}"):
                            render_voting_modal(m, "FOR")
                    with col_b:
                        if st.button(f"Vote AGAINST", key=f"against_{m['id']}"):
                            render_voting_modal(m, "AGAINST")

    # --- TAB 3: TIER MATRIX ---
    with tab3:
        st.header("Stewardship Tier Structure")
        
        tier_data = pd.DataFrame({
            "Tier Level": ["Gamma Steward", "Beta Steward", "Alpha Steward", "Omega Steward"],
            "Governance Points": ["0 - 49 pts", "50 - 99 pts", "100 - 149 pts", "150+ pts"],
            "Voting Weight": ["1.0x", "1.2x", "1.5x", "2.0x"],
            "Escrow Multiplier": ["1.0x", "1.1x", "1.25x", "1.5x"],
            "Perks": [
                "Basic voting access",
                "Monthly governance reports",
                "Priority proxy representation & higher rewards",
                "Direct advisory access & governance board seat eligibility"
            ]
        })
        
        st.table(tier_data)

    # --- TAB 4: LEDGER ---
    with tab4:
        st.header("Reward & Activity Ledger")
        
        conn = sqlite3.connect("investor_trust.db")
        
        st.subheader("Quiz Rewards History")
        df_quiz = pd.read_sql_query("SELECT id, date, score, reward FROM quiz_history ORDER BY date DESC", conn)
        if not df_quiz.empty:
            df_quiz['reward'] = df_quiz['reward'].apply(lambda x: f"₹{x}")
            st.dataframe(df_quiz, use_container_width=True)
        else:
            st.write("No quiz history found.")
            
        st.subheader("Governance Voting History")
        df_votes = pd.read_sql_query("SELECT id, mandate_id, company, proposal, vote, reward FROM governance_votes", conn)
        if not df_votes.empty:
            df_votes['reward'] = df_votes['reward'].apply(lambda x: f"₹{x}")
            st.dataframe(df_votes, use_container_width=True)
        else:
            st.write("No voting history found.")
            
        conn.close()
