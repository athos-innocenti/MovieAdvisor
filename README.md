# 🎬 Movie Advisor AI-powered Movie Recommendation System

Film Advisor is a Python-based intelligent movie recommendation system that combines **Generative AI (Gemini)** with **structured data from TMDB (The Movie Database)** to deliver contextual, explainable, and actionable film suggestions.

The goal is simple: turn a vague idea into a curated list of movies and tell you exactly where to watch them.

------------------------------------------------------------------------

## ✨ Key Features

### 🧠 Natural Language Understanding

Users can describe what they want to watch using **free-form text**:
- moods (*"something intense and psychological"*)
- constraints (*"movies from the 2000s"*)
- mixed requirements (*"3 highly rated thrillers that keep me hooked"*)

The system interprets the request semantically, not just through keyword
matching.

------------------------------------------------------------------------

### 🎯 Advanced Filtering via Prompt

The system supports **dynamic constraints directly embedded in the
input**, including:

-   Number of movies to return
-   Time constraints (year, ranges, decades)
-   Sorting criteria (e.g. by rating or release year)
-   Combined filters (e.g. *"top 5 dramas after 2010 sorted by rating"*)

------------------------------------------------------------------------

### 🤖 AI Reasoning Layer (Gemini)

Gemini is responsible for:
- Understanding user intent
- Selecting coherent movie suggestions
- Generating **human-like explanations** for each recommendation

------------------------------------------------------------------------

### 📊 Data Enrichment via TMDB API

Each AI-generated suggestion is enriched with real-world data using
TMDB:

-   Title and release year
-   Rating (TMDB score)
-   Official plot
-   Streaming availability, rental, and purchase options

------------------------------------------------------------------------

### 📺 Actionable Output

The output is not just descriptive, it is **immediately usable**:

-   What to watch
-   Why it fits your request
-   Where to watch it (streaming / rent / buy)

------------------------------------------------------------------------

## 🏗️ Architecture

The system follows a **modular and layered architecture**, separating
reasoning from data retrieval.

### Flow Overview

User Input

↓

Gemini (reasoning & generation)

↓

Film Advisor (orchestration layer) ⇄ TMDB API (data enrichment)

↓

Output (final structured response)

------------------------------------------------------------------------

### 🔍 Component Breakdown

#### 1. User Input

-   Free-text description of the desired movie experience

#### 2. Gemini (LLM Layer)

-   Interprets intent
-   Generates structured recommendations
-   Produces explanations

#### 3. Film Advisor (Orchestrator)

-   Coordinates the pipeline
-   Parses Gemini output
-   Applies constraints and formatting
-   Calls external APIs

#### 4. TMDB (Data Layer)

-   Provides reliable, structured movie data
-   Supports:
    -   Search
    -   Metadata retrieval
    -   Watch providers (streaming platforms)

#### 5. Output Layer

-   Merges AI reasoning with real data
-   Produces a clean, readable result

------------------------------------------------------------------------

## ⚙️ Tech Stack

-   Python
-   Gemini API (Google AI)
-   TMDB API
-   CLI-based interface (current version)

------------------------------------------------------------------------

## 📌 Design Principles

-   Separation of concerns
-   Explainability
-   User-centric interaction
-   Actionability

------------------------------------------------------------------------

## 🔮 Future Improvements

This project is currently:

-   Developed in Italian
-   Available as a Python script

### Planned Evolution

-   Full CLI application with conversational context
-   Multi-turn interaction (not just single-shot responses)
-   Optional web search integration
-   Multi-language support

------------------------------------------------------------------------

## 💡 Motivation

This project was born from a simple, real-world problem:

A Tuesday night, no idea what to watch, and too many options.

Movie Advisor aims to bridge the gap between: inspiration (AI), availability (platforms) and decision (user)

------------------------------------------------------------------------

## 📬 Feedback

Feel free to open issues, suggest improvements, or contribute.
