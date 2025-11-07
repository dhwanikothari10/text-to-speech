import streamlit as st
import requests
from langchain_google_genai import ChatGoogleGenerativeAI
from gtts import gTTS
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# --------------------- FUNCTIONS ---------------------

def fetch_news(topic):
    url = f"https://newsapi.org/v2/everything?q={topic}&language=en&apiKey={NEWS_API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        return None, f"❌ Error fetching news: {response.text}"

    data = response.json()
    articles = data.get("articles", [])
    if not articles:
        return None, "⚠️ No news articles found for this topic."

    main_topic = articles[0]["title"]
    news_text = "\n".join([f"{a['title']}. {a['description']}" for a in articles[:5] if a["description"]])
    return (main_topic, news_text)

def summarize_text(text):
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)
    summary = llm.invoke(f"Summarize these news headlines for a natural narration:\n{text}")
    return summary.content

def text_to_speech(text, topic, folder="output_audio"):
    os.makedirs(folder, exist_ok=True)
    safe_topic = "".join(c if c.isalnum() or c in (" ", "_", "-") else "" for c in topic)
    filename = os.path.join(folder, f"{safe_topic[:50]}.mp3")

    narration = f"Topic is: {topic}. Let's start. {text}"
    tts = gTTS(text=narration, lang="en")
    tts.save(filename)

    return filename

# --------------------- STREAMLIT UI ---------------------

st.set_page_config(page_title="AI News Reader", page_icon="📰", layout="centered")

st.title("📰 AI News Reader")
st.write("Enter a topic to fetch the latest news, summarize it, and listen to the narration!")

user_topic = st.text_input("🔍 Enter a topic:", placeholder="e.g. Artificial Intelligence, Space, Technology")

if st.button("Fetch & Summarize News"):
    if not user_topic.strip():
        st.warning("Please enter a topic first.")
    else:
        with st.spinner("Fetching latest news..."):
            result = fetch_news(user_topic)
            if result is None or result[0] is None:
                st.error(result[1] if result else "Error fetching news.")
            else:
                main_topic, news_text = result
                st.success("✅ News fetched successfully!")

                st.subheader("🗞️ Main Topic")
                st.write(main_topic)

                st.subheader("📰 Top Headlines")
                st.text_area("News Headlines", news_text, height=200)

                with st.spinner("Summarizing with Gemini..."):
                    summary = summarize_text(news_text)
                    st.subheader("🧠 Summary")
                    st.write(summary)

                with st.spinner("Converting summary to speech..."):
                    audio_file = text_to_speech(summary, user_topic)
                    st.success("✅ Audio generated successfully!")

                # Play audio directly in Streamlit
                audio_bytes = open(audio_file, "rb").read()
                st.audio(audio_bytes, format="audio/mp3")

st.markdown("---")
st.caption("Developed with ❤️ using Streamlit, LangChain, Google Gemini, and gTTS.")
