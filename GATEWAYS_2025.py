import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import re
import json

# Set page config

st.set_page_config(page_title="GATEWAYS-2025 Dashboard", page_icon="🎉", layout="wide")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('Fest_dataset.csv')
    return df

# State name mapping for GeoJSON compatibility
state_mapping = {
    'Telangana': 'Andhra Pradesh',  # Telangana might not be in older GeoJSON
    # Add more mappings if needed
}

def map_state_name(state):
    """Map state names to match GeoJSON"""
    return state_mapping.get(state, state)

df = load_data()

# Title
st.title("GATEWAYS-2025 National Level Fest Dashboard")
st.markdown("---")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Overview", "Participation Analysis", "Feedback Analysis"])

if page == "Overview":
    st.header("Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Participants", len(df))
    
    with col2:
        st.metric("Total Colleges", df['College'].nunique())
    
    with col3:
        st.metric("Total Events", df['Event Name'].nunique())
    
    with col4:
        st.metric("Total States", df['State'].nunique())
    
    st.markdown("### Event Types Distribution")
    event_type_counts = df['Event Type'].value_counts()
    fig = px.pie(values=event_type_counts.values, names=event_type_counts.index, title="Event Types")
    st.plotly_chart(fig)
    
    st.markdown("### Top 10 Colleges by Participation")
    college_counts = df['College'].value_counts().head(10)
    fig = px.bar(x=college_counts.index, y=college_counts.values, title="Top 10 Colleges")
    st.plotly_chart(fig)

elif page == "Participation Analysis":
    st.header("Participation Analysis")
    
    # State-wise participants on India map
    st.subheader("State-wise Participants on India Map")
    state_counts = df['State'].value_counts().reset_index()
    state_counts.columns = ['State', 'Participants']
    
    # Map state names to match GeoJSON
    state_counts['State'] = state_counts['State'].apply(map_state_name)
    state_counts = state_counts.groupby('State')['Participants'].sum().reset_index()
    
    # Load GeoJSON and create choropleth
    try:
        with open('Indian_States.geojson', 'r') as f:
            geojson_data = json.load(f)
        
        # Create choropleth map
        fig = px.choropleth(
            state_counts,
            geojson=geojson_data,
            featureidkey='properties.NAME_1',
            locations='State',
            color='Participants',
            color_continuous_scale="Viridis",
            title="State-wise Participation in GATEWAYS-2025",
            hover_name='State',
            hover_data={'Participants': True, 'State': False}
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        # Display table of state-wise data
        st.subheader("State-wise Participation Data")
        st.dataframe(state_counts.sort_values('Participants', ascending=False))
        
    except FileNotFoundError:
        st.error("❌ GeoJSON file 'india_state_geo.json' not found. Please ensure it's in the project folder.")
        # Fallback: Show bar chart
        st.subheader("State-wise Participants (Bar Chart)")
        fig = px.bar(state_counts.sort_values('Participants', ascending=False), 
                     x='State', y='Participants', title="Participants per State",
                     color='Participants', color_continuous_scale="Viridis")
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Error loading map: {str(e)}")
        # Fallback: Show bar chart
        st.subheader("State-wise Participants (Bar Chart)")
        fig = px.bar(state_counts.sort_values('Participants', ascending=False), 
                     x='State', y='Participants', title="Participants per State",
                     color='Participants', color_continuous_scale="Viridis")
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    # Event-wise analysis
    st.subheader("Event-wise Participation")
    event_counts = df['Event Name'].value_counts().reset_index()
    event_counts.columns = ['Event', 'Participants']
    fig = px.bar(event_counts, x='Event', y='Participants', 
                 title="Participants per Event", color='Participants',
                 color_continuous_scale="Viridis")
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(event_counts)
    with col2:
        fig_pie = px.pie(event_counts, values='Participants', names='Event', 
                        title="Event Distribution")
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # College-wise analysis
    st.subheader("College-wise Participation")
    college_counts = df['College'].value_counts().reset_index()
    college_counts.columns = ['College', 'Participants']
    
    col1, col2 = st.columns([3, 1])
    with col1:
        fig = px.bar(college_counts.head(20), x='College', y='Participants', 
                     title="Top 20 Colleges by Participation",
                     color='Participants', color_continuous_scale="Viridis")
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.metric("Total Colleges", college_counts.shape[0])
        st.metric("Top College", college_counts.iloc[0]['College'])
        st.metric("Top College Count", college_counts.iloc[0]['Participants'])
    
    st.dataframe(college_counts.head(15), use_container_width=True)
    
    # Amount Paid analysis
    st.subheader("Revenue Analysis")
    total_revenue = df['Amount Paid'].sum()
    st.metric("Total Revenue", f"₹{total_revenue}")
    
    revenue_by_event = df.groupby('Event Name')['Amount Paid'].sum().reset_index().sort_values('Amount Paid', ascending=False)
    fig = px.bar(revenue_by_event, x='Event Name', y='Amount Paid', 
                 title="Revenue by Event", color='Amount Paid',
                 color_continuous_scale="Greens")
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

elif page == "Feedback Analysis":
    st.header("Feedback Analysis")
    
    # Rating statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Avg Rating", f"{df['Rating'].mean():.2f}/5")
    with col2:
        st.metric("Total Feedbacks", len(df))
    with col3:
        st.metric("Highest Rating %", f"{(df['Rating'] == 5).sum() / len(df) * 100:.1f}%")
    with col4:
        st.metric("Lower Ratings %", f"{(df['Rating'] <= 3).sum() / len(df) * 100:.1f}%")
    
    st.markdown("---")
    
    # Ratings distribution
    st.subheader("Ratings Distribution")
    rating_counts = df['Rating'].value_counts().sort_index()
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(x=rating_counts.index, y=rating_counts.values, 
                     title="Number of Participants by Rating",
                     labels={'x': 'Rating', 'y': 'Count'},
                     color=rating_counts.index,
                     color_continuous_scale="RdYlGn")
        fig.update_xaxes(tickmode='linear')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.pie(values=rating_counts.values, names=rating_counts.index,
                    title="Rating Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    # Average rating by event
    st.subheader("Average Rating by Event")
    avg_rating_event = df.groupby('Event Name')['Rating'].mean().reset_index().sort_values('Rating', ascending=False)
    fig = px.bar(avg_rating_event, x='Event Name', y='Rating', 
                 title="Average Rating per Event (Higher is Better)",
                 color='Rating', color_continuous_scale="RdYlGn",
                 range_color=[1, 5])
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Feedback text analysis
    st.subheader(" Feedback Text Analysis")
    
    # Combine all feedback
    all_feedback = ' '.join(df['Feedback on Fest'].dropna())
    
    # Clean text
    all_feedback_clean = re.sub(r'[^\w\s]', '', all_feedback).lower()
    
    # Word frequency
    words = all_feedback_clean.split()
    word_freq = Counter(words)
    
    # Remove common words
    common_words = ['and', 'the', 'to', 'a', 'of', 'in', 'for', 'with', 'on', 'by', 'at', 'from', 'as', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'or', 'not', 'session']
    for word in common_words:
        if word in word_freq:
            del word_freq[word]
    
    # Top words
    top_words = dict(word_freq.most_common(20))
    top_words_df = pd.DataFrame(list(top_words.items()), columns=['Word', 'Frequency'])
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(top_words_df, x='Word', y='Frequency', 
                     title="Top 20 Words in Feedback",
                     color='Frequency', color_continuous_scale="Blues")
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        # Word cloud
        if all_feedback_clean.strip():
            wordcloud = WordCloud(width=800, height=400, background_color='white', 
                                 colormap='viridis').generate(all_feedback_clean)
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)
    
    # Feedback by rating
    st.subheader("Participant Feedback by Rating")
    rating_tabs = st.tabs([f"{i}-Star" for i in range(5, 0, -1)])
    for idx, rating in enumerate(range(5, 0, -1)):
        with rating_tabs[idx]:
            feedback_data = df[df['Rating'] == rating][['Student Name', 'College', 'Event Name', 'Feedback on Fest']]
            if len(feedback_data) > 0:
                st.metric(f"Total {rating}-star feedback", len(feedback_data))
                st.dataframe(feedback_data, use_container_width=True)
            else:
                st.info(f"No {rating}-star feedback")
    
    # Show all feedback
    st.subheader(" All Feedback Data")
    st.dataframe(df[['Student Name', 'College', 'Event Name', 'Feedback on Fest', 'Rating']],
                use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
### Key Insights Summary
- **Participation**: Analyze participation trends across states, colleges, and events
- **Ratings**: Understand participant satisfaction through ratings and feedback
- **Feedback**: Extract actionable insights from participant feedback
- **Revenue**: Track financial performance across different events

*Developed for GATEWAYS-2025 National Level Fest Organizing Team*
""")
