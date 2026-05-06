from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

import os
import pickle
import io
import streamlit as st
import pandas as pd
from datetime import datetime
import csv

# -------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------
st.set_page_config(
    page_title="ICMAAM'24 Submission Portal",
    page_icon="📘",
    layout="centered"
)

# -------------------------------------------------------
# CUSTOM CSS
# -------------------------------------------------------
st.markdown("""
<style>

/* Main Background */
.stApp {
    background-color: #f4f6f9;
}

/* Main Container */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 850px;
}

/* Header */
.main-title {
    text-align: center;
    color: #003366;
    font-size: 42px;
    font-weight: 700;
    margin-bottom: 0px;
}

.sub-title {
    text-align: center;
    color: #555555;
    font-size: 28px;
    margin-top: -5px;
}

.portal-title {
    text-align: center;
    color: #990000;
    font-size: 30px;
    font-weight: 600;
    margin-top: 10px;
    margin-bottom: 30px;
}

/* Cards */
.card {
    background-color: white;
    color: #222222;
    padding: 28px;
    border-radius: 14px;
    box-shadow: 0px 2px 10px rgba(0,0,0,0.08);
    margin-bottom: 25px;
    border: 1px solid #e5e7eb;
}

/* Section Header */
.section-title {
    color: #003366;
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 15px;
}

/* Metadata Box */
.meta-box {
    background-color: #eef4ff;
    color: #111111;
    padding: 14px;
    border-radius: 10px;
    border-left: 5px solid #003366;
    margin-top: 10px;
    margin-bottom: 10px;
}

/* Small Text */
.small-text {
    color: #666666;
    font-size: 14px;
}

/* Divider */
hr {
    margin-top: 10px;
    margin-bottom: 25px;
}

</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# HEADER
# -------------------------------------------------------
st.markdown("""
<div class="main-title">
Springer Book Proceedings
</div>

<div class="sub-title">
ICMAAM'24
</div>

<div class="portal-title">
Final Manuscript Submission Portal
</div>

<hr>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# INSTRUCTIONS CARD
# -------------------------------------------------------
st.markdown("""
<div class="card">

<div class="section-title">
📌 Instructions for Corresponding Authors
</div>

<ul>
<li>Enter your assigned submission code and corresponding author email.</li>
<li>The system will automatically validate your manuscript information.</li>
<li>Please upload ALL mandatory files.</li>
<li>Accepted file formats: PDF, DOCX, TEX, ZIP</li>
<li>Ensure that uploaded files are final revised versions.</li>
</ul>

</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# LOAD CSV DATABASE
# -------------------------------------------------------
try:
    df = pd.read_csv("authors.csv")

except FileNotFoundError:
    st.error("❌ authors.csv file not found.")
    st.stop()

# -------------------------------------------------------
# GOOGLE DRIVE AUTHENTICATION
# -------------------------------------------------------
SCOPES = ['https://www.googleapis.com/auth/drive']

creds = None

if os.path.exists('token.pickle'):

    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

if not creds or not creds.valid:

    if creds and creds.expired and creds.refresh_token:

        creds.refresh(Request())

    else:

        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json',
            SCOPES
        )

        creds = flow.run_local_server(port=0)

    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('drive', 'v3', credentials=creds)

ROOT_FOLDER_ID = "1j_S5h0ZhTvoTqoDLtZ62bEUuHK-547op"

# -------------------------------------------------------
# GOOGLE DRIVE UPLOAD FUNCTION
# -------------------------------------------------------
def upload_to_drive(file_data, filename, folder_id):

    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }

    media = MediaIoBaseUpload(
        io.BytesIO(file_data),
        mimetype='application/octet-stream'
    )

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    return uploaded_file.get('id')

# -------------------------------------------------------
# CREATE GOOGLE DRIVE FOLDER
# -------------------------------------------------------
def create_folder(folder_name, parent_id):

    query = (
        f"name='{folder_name}' and "
        f"'{parent_id}' in parents and trashed=false"
    )

    results = service.files().list(
        q=query,
        fields='files(id, name)'
    ).execute()

    items = results.get('files', [])

    if items:
        return items[0]['id']

    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }

    folder = service.files().create(
        body=file_metadata,
        fields='id'
    ).execute()

    return folder.get('id')

# -------------------------------------------------------
# AUTHOR VERIFICATION
# -------------------------------------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)

st.markdown("""
<div class="section-title">
🔐 Author Verification
</div>
""", unsafe_allow_html=True)

submission_code = st.text_input(
    "Submission Code",
    placeholder="Example: 3-V1"
)

email = st.text_input(
    "Corresponding Author Email",
    placeholder="example@email.com"
)

verified = False

author_name = ""
volume = ""
subject_domain = ""

# -------------------------------------------------------
# VALIDATION
# -------------------------------------------------------
if submission_code and email:

    match = df[
        (df["submission_code"].astype(str).str.strip() == submission_code.strip()) &
        (df["email"].astype(str).str.strip().str.lower() == email.strip().lower())
    ]

    if len(match) == 1:

        verified = True

        author_name = match.iloc[0]["author"]
        volume = match.iloc[0]["volume"]
        subject_domain = match.iloc[0]["subject_domain"]

        st.success("✅ Author verified successfully.")

        st.markdown(f"""
<div class="meta-box">

<b>Author:</b> {author_name}<br>
<b>Subject Domain:</b> {subject_domain}<br>
<b>Assigned Volume:</b> {volume}

</div>
""", unsafe_allow_html=True)

    else:

        st.error(
            "❌ Invalid submission code or email."
        )

st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------
# FILE UPLOAD SECTION
# -------------------------------------------------------
if verified:

    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.markdown("""
<div class="section-title">
📂 Upload Mandatory Files
</div>
""", unsafe_allow_html=True)

    final_manuscript = st.file_uploader(
        "1️⃣ Final Manuscript",
        type=["pdf", "docx", "tex"]
    )

    review_response = st.file_uploader(
        "2️⃣ Response to Reviewer",
        type=["pdf", "docx"]
    )

    source_files = st.file_uploader(
        "3️⃣ Source Files (.zip/.tex/.docx)",
        type=["zip", "tex", "docx"],
        accept_multiple_files=True
    )

    st.markdown("""
<p class="small-text">
All three uploads are mandatory for final submission.
</p>
""", unsafe_allow_html=True)

    # -------------------------------------------------------
    # SUBMIT BUTTON
    # -------------------------------------------------------
    if st.button("📤 Submit Final Files"):

        # Validation
        if final_manuscript is None:
            st.error("Final manuscript is required.")
            st.stop()

        if review_response is None:
            st.error("Reviewer response is required.")
            st.stop()

        if not source_files:
            st.error("Source files are required.")
            st.stop()

        # Timestamp
        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # -------------------------------------------------------
        # CREATE GOOGLE DRIVE FOLDERS
        # -------------------------------------------------------
        volume_folder_id = create_folder(
            volume,
            ROOT_FOLDER_ID
        )

        final_folder_id = create_folder(
            "Final_Manuscript",
            volume_folder_id
        )

        response_folder_id = create_folder(
            "Response_to_Reviewer",
            volume_folder_id
        )

        source_folder_id = create_folder(
            "Source_Files",
            volume_folder_id
        )

        # -------------------------------------------------------
        # FILE NAMES
        # -------------------------------------------------------
        final_filename = (
            f"{submission_code}_final_{final_manuscript.name}"
        )

        response_filename = (
            f"{submission_code}_response_{review_response.name}"
        )

        # -------------------------------------------------------
        # UPLOAD FINAL MANUSCRIPT
        # -------------------------------------------------------
        upload_to_drive(
            final_manuscript.getvalue(),
            final_filename,
            final_folder_id
        )

        # -------------------------------------------------------
        # UPLOAD REVIEW RESPONSE
        # -------------------------------------------------------
        upload_to_drive(
            review_response.getvalue(),
            response_filename,
            response_folder_id
        )

        # -------------------------------------------------------
        # UPLOAD SOURCE FILES
        # -------------------------------------------------------
        for uploaded_file in source_files:

            source_filename = (
                f"{submission_code}_source_{uploaded_file.name}"
            )

            upload_to_drive(
                uploaded_file.getvalue(),
                source_filename,
                source_folder_id
            )

        # -------------------------------------------------------
        # SAVE METADATA
        # -------------------------------------------------------
        metadata_file = "submission_metadata.csv"

        file_exists = False

        try:
            with open(metadata_file, "r"):
                file_exists = True

        except FileNotFoundError:
            pass

        with open(
            metadata_file,
            "a",
            newline="",
            encoding="utf-8"
        ) as csvfile:

            writer = csv.writer(csvfile)

            if not file_exists:

                writer.writerow([
                    "submission_code",
                    "author",
                    "email",
                    "volume",
                    "subject_domain",
                    "timestamp"
                ])

            writer.writerow([
                submission_code,
                author_name,
                email,
                volume,
                subject_domain,
                timestamp
            ])

        # -------------------------------------------------------
        # SUCCESS MESSAGE
        # -------------------------------------------------------
        st.success(
            "✅ Final manuscript files submitted successfully."
        )

        st.balloons()

        st.markdown(f"""
<div class="meta-box">

<h4>Submission Summary</h4>

<b>Submission Code:</b> {submission_code}<br>
<b>Author:</b> {author_name}<br>
<b>Volume:</b> {volume}<br>
<b>Subject Domain:</b> {subject_domain}<br>
<b>Submission Time:</b> {timestamp}

</div>
""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
