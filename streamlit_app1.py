import os
import uuid
import random
import streamlit as st
import boto3
import requests
from urllib.parse import urlparse
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ----------- Initialize AzureOpenAI client globally -------------
client = AzureOpenAI(
    api_key="BdF3fgzjYDE5j2WfQLh4uxblwoBN4OgooER86XJI7cx37R8Ku46LJQQJ99AKACYeBjFXJ3w3AAAAACOGYNrN",
    azure_endpoint="https://suvichaarai008818057333687.openai.azure.com/",
    api_version="2025-01-01-preview",
)

# ----------- AWS S3 Config from env -------------
aws_access_key = os.getenv("AWS_ACCESS_KEY")
aws_secret_key = os.getenv("AWS_SECRET_KEY")
region_name = os.getenv("AWS_REGION")
bucket_name = os.getenv("AWS_BUCKET")
s3_prefix = os.getenv("S3_PREFIX")
cdn_base_url = os.getenv("CDN_BASE")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=region_name,
)

# ----------- Sidebar: Azure OpenAI Chat UI -------------
with st.sidebar:
    st.header("Azure OpenAI Chat")
    user_question = st.text_input("Your question:")

    if st.button("Send"):
        if user_question.strip() == "":
            st.warning("Please enter a question.")
        else:
            with st.spinner("Waiting for response..."):
                messages = [{"role": "user", "content": user_question}]
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    max_tokens=1500,
                    temperature=0.5,
                )
                answer = response.choices[0].message.content
                st.success("Answer:")
                st.write(answer)

# ----------- Main content: Metadata form, image URL upload, HTML upload -------------
st.title("Content Submission Form")

with st.form(key="content_form"):
    story_title = st.text_input("Story Title")
    meta_description = st.text_area("Meta Description")
    meta_keywords = st.text_input("Meta Keywords (comma separated)")
    image_url = st.text_input("Image URL to upload to S3")
    html_file = st.file_uploader("Upload your Raw HTML File", type=["html", "htm"])
    submit_button = st.form_submit_button("Submit")

if submit_button:
    st.markdown("### Submitted Data")
    st.write(f"**Story Title:** {story_title}")
    st.write(f"**Meta Description:** {meta_description}")
    st.write(f"**Meta Keywords:** {meta_keywords}")

    uploaded_url = None  # Initialize for fallback

    # 1. Process image upload
    if image_url:
        try:
            response = requests.get(image_url)
            response.raise_for_status()

            parsed_url = urlparse(image_url)
            filename = os.path.basename(parsed_url.path)
            ext = os.path.splitext(filename)[1].lower()
            if ext not in [".jpg", ".jpeg", ".png", ".gif"]:
                ext = ".jpg"

            unique_filename = f"{uuid.uuid4().hex}{ext}"
            s3_key = f"{s3_prefix}{unique_filename}"

            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=response.content,
                ContentType=response.headers.get("Content-Type", "image/jpeg"),
            )

            uploaded_url = f"{cdn_base_url}{s3_key}"
            st.success("Image uploaded successfully!")
            st.write("CDN URL:")
            st.write(uploaded_url)
            st.image(uploaded_url, caption="Uploaded Image Preview", use_container_width=True)

        except Exception as e:
            st.error(f"Failed to upload image: {e}")
    else:
        st.info("No Image URL provided.")

    # 2. Load and process masterregex.html
    try:
        local_file_path = r"C:\Users\DLPS\OneDrive\Desktop\StoriesLab\masterregex.html"
        with open(local_file_path, "r", encoding="utf-8") as file:
            html_template = file.read()

        # Replace {{user}} with a random name
        selected_user = random.choice(["Onip", "Naman", "Mayank"])
        html_template = html_template.replace("{{user}}", selected_user)

        # Replace {{image0}} with media.suvichaar.org image URL
        if uploaded_url:
            media_url = uploaded_url.replace("https://cdn.", "https://media.")
        else:
            media_url = "https://media.suvichaar.org/media/default.png"

        html_template = html_template.replace("{{image0}}", media_url)

        # Show final HTML
        st.markdown("### Final Modified HTML")
        st.code(html_template, language="html")

    except Exception as e:
        st.error(f"Error processing masterregex.html: {e}")

    # 3. Optional user-uploaded HTML
    if html_file:
        raw_html = html_file.read().decode("utf-8")
        st.markdown("### Raw Uploaded HTML")
        st.code(raw_html, language="html")
    else:
        st.info("No HTML file uploaded.")
