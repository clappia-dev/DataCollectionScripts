# Reddit Topic Analyzer for Competitor Research
#
# This script analyzes Reddit discussions about competitor platforms to:
#   1. Identify feature gaps and user pain points
#   2. Generate ideas for product improvements
#   3. Stay updated on industry trends and user needs
#

# How to run:
# 1. Install required packages: pip install -r requirements.txt
# 2. Set up a .env file with the following variables:
#    REDDIT_CLIENT_ID=your_reddit_client_id
#    REDDIT_CLIENT_SECRET=your_reddit_client_secret
#    REDDIT_USER_AGENT=your_reddit_user_agent
#    OPENAI_API_KEY=your_openai_api_key
# 3. Run the script: python analyze-reddit-topic.py

import praw
import openai
import os
import json
import random
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up Reddit API client
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

# Set up OpenAI API client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_post(subreddit_name, title, body, comments, my_platform):
    """
    Analyze a Reddit post using OpenAI's GPT model.
    
    :param subreddit_name: Name of the subreddit
    :param title: Title of the post
    :param body: Body of the post
    :param comments: Comments on the post
    :param my_platform: Name of the competitor platform
    :return: Dictionary containing analysis results
    """
    system_message = f"""You are an AI assistant that analyzes Reddit posts about {subreddit_name} and generates competitor-related questions for the platform {my_platform}. Your responses must adhere to the following rules:
    1. Always respond with a valid JSON object containing the keys: "summary", "status", and optionally "question1", "question2", "question3".
    2. Each question must be complete, mentioning both {subreddit_name} and the competitor platform {my_platform}.
    3. Only include question fields if the status is "feature_not_supported" or "feature_supported_but_not_easy_to_use".
    4. Phrase each question from the user's perspective, first mentioning the issue or limitation in {subreddit_name}, then asking if the competitor platform {my_platform} provides support for it.
    5. Use this format for questions: "I am facing [problem] in {subreddit_name}. Does {my_platform} provide support for [feature] (or make it easier)?"
    """

    prompt = f"""
    Analyze the following Reddit post and its comments, then provide:
    1. A one-line summary of the topic being discussed, phrased as a question.
    2. Whether the post is discussing an {subreddit_name} feature, and if so, whether {subreddit_name} supports it.
    Use one of these statuses:
    - "feature_supported": The feature is supported by {subreddit_name}
    - "feature_not_supported": The feature is not supported by  {subreddit_name}
    - "feature_supported_but_not_easy_to_use": The feature is supported but difficult to implement
    - "not_relevant": The post is not discussing a specific  {subreddit_name} feature

    3. If the status is "feature_not_supported" or "feature_supported_but_not_easy_to_use", provide 3 complete questions to ask about competitor {my_platform}. Each question should first mention the issue in {subreddit_name}, then ask if it's possible or easier to achieve in {my_platform}.

    Title: {title}
    Body: {body}
    Comments:
    {comments}

    Respond with a JSON object in the following format:
    {{
        "summary": "<one-line summary as a question>",
        "status": "<feature status>",
        "question1": "<complete competitor question 1>",
        "question2": "<complete competitor question 2>",
        "question3": "<complete competitor question 3>"
    }}

    Note: Include the question fields only if the status is "feature_not_supported" or "feature_supported_but_not_easy_to_use". Each question should be from the user's perspective, mentioning the {subreddit_name} issue first, then asking about {my_platform}.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.choices[0].message.content.strip()
        return parse_openai_response(content)
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        return {}

def parse_openai_response(content):
    """
    Parse the OpenAI API response and extract the JSON content.
    
    :param content: Raw content from OpenAI API response
    :return: Parsed JSON as a dictionary
    """
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        json_match = re.search(r'\{[\s\S]*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                print("Failed to extract valid JSON from the response.", content)
        else:
            print("No JSON-like content found in the response.", content)
    return {}

def analyze_reddit_topics(subreddit_names, my_platform, output_file, max_posts=10):
    """
    Analyze Reddit topics from multiple subreddits.
    
    :param subreddit_names: List of subreddit names to analyze
    :param my_platform: Name of the competitor platform
    :param output_file: Name of the output file
    :param max_posts: Maximum number of posts to analyze per subreddit
    """
    all_results = [] 
    for subreddit_name in subreddit_names:
        subreddit = reddit.subreddit(subreddit_name)
        posts_analyzed = 0
        
        for post in subreddit.new(limit=None):
            if posts_analyzed >= max_posts:
                break
            
            print(f"\nAnalyzing post: {post.title}")
            
            post.comments.replace_more(limit=0)
            comments = "\n".join([f"{comment.author}: {comment.body}" for comment in post.comments.list()])
            
            analysis = analyze_post(subreddit_name, post.title, post.selftext, comments, my_platform)
            if analysis and "summary" in analysis and "status" in analysis:
                result = create_result_dict(subreddit_name, post, analysis)
                all_results.append(result)
                posts_analyzed += 1
            
                update_files(all_results, output_file)
                
                print(json.dumps(analysis, indent=2))

def create_result_dict(subreddit_name, post, analysis):
    """
    Create a dictionary with the analysis results.
    
    :param subreddit_name: Name of the subreddit
    :param post: Reddit post object
    :param analysis: Analysis results from OpenAI
    :return: Dictionary with formatted results
    """
    result = {
        "subreddit": subreddit_name,
        "postUrl": f"https://www.reddit.com{post.permalink}",
        "postTitle": post.title,
        "summary": analysis["summary"],
        "status": analysis["status"]
    }
    
    if analysis["status"] in ["feature_not_supported", "feature_supported_but_not_easy_to_use"]:
        for i in range(1, 4):
            question_key = f"question{i}"
            if question_key in analysis and analysis[question_key]:
                result[question_key] = analysis[question_key]
    
    return result

def update_files(results, output_file):
    """
    Update the JSON file with all results.
    
    :param results: List of all analysis results
    """
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    # subreddit_names = ["AppSheet", "glideapps", "Bubbleio", "zohocreator"]
    my_platform = input("Enter the name of your platform: ")
    subreddit_names = input("Enter the names of the subreddits to analyze (comma-separated, no spaces): ").split(',')
    output_file = input("Enter the name of the output JSON file: ")
    analyze_reddit_topics(subreddit_names, my_platform, output_file)
