#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct  3 16:35:47 2024
#System Final
@author: peiyan
"""


import openai
import sounddevice as sd
import soundfile as sf
import numpy as np
import wave
import random
import speech_recognition as sr
import subprocess
import os
import sys

# Set your working directory if needed
os.chdir('your working directory')

# Set OpenAI API key
openai.api_key = "your openAI key"
model_id = 'gpt-4'

# Counter for interaction purposes
interaction_counter = 0

def transcribe_audio_to_text(filename):
    recognizer = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            print("Could not understand audio.")
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
    return ""

def ChatGPT_conversation(conversation):
    response = openai.chat.completions.create(
        model=model_id,
        messages=conversation
    )
    # Access token usage attributes directly
    total_tokens = response.usage.total_tokens
    print(f"Total tokens consumed: {total_tokens}")
    
    # Access the response message
    conversation.append({
        'role': response.choices[0].message.role,
        'content': response.choices[0].message.content
    })
    return conversation

def speak_text(text):
    subprocess.call(['say', text])

def record_audio(filename, duration=6, sample_rate=44100):
    print("Recording...")
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()
    audio_data = audio_data.flatten()

    # Save audio data as a .wav file
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 'int16' corresponds to 2 bytes
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())
    print("Recording complete.")

def activate_assistant():
    starting_chat_phrases = [
        "Yes boss, how may I assist you?",
        "Yes, what can I do for you?",
        "How can I help you?",
        "Grammar at your service, what do you need?",
        "Grammar here, how can I help you today?"
    ]
    continued_chat_phrases = ["Yes", "Yes, boss", "I'm all ears"]

    if interaction_counter == 1:
        return random.choice(starting_chat_phrases)
    else:
        return random.choice(continued_chat_phrases)

def append_to_log(text):
    with open("chat_log.txt", "a") as f:
        f.write(text + "\n")

def listen_for_wake_word(wake_word='grammar', sample_rate=16000, duration=4):
    recognizer = sr.Recognizer()
    print(f"Listening for wake word '{wake_word}'...")

    while True:
        # Capture audio using sounddevice
        print("Recording for wake word...")
        try:
            audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
            sd.wait()
            audio_data = np.array(audio_data).flatten()
        except Exception as e:
            print(f"Error recording audio: {e}")
            continue

        # Save to temporary .wav file
        temp_filename = 'temp_wake_word.wav'
        try:
            with wave.open(temp_filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data.tobytes())
        except Exception as e:
            print(f"Error saving audio to file: {e}")
            continue

        # Use Google Speech Recognition to process audio
        with sr.AudioFile(temp_filename) as source:
            audio = recognizer.record(source)
            try:
                transcription = recognizer.recognize_google(audio)
                print(f"Heard: '{transcription}'")

                # Check if the wake word is in the transcription
                if wake_word.lower() in transcription.lower():
                    print(f"Wake word '{wake_word}' detected.")
                    os.remove(temp_filename)
                    return  # Successfully detected wake word, exit loop

            except sr.UnknownValueError:
                print("Could not understand audio, retrying...")
            except sr.RequestError as e:
                print(f"Could not request results; check your internet connection. Error: {e}")

        os.remove(temp_filename)  # Clean up temporary file

# Define your conversation with a system prompt
conversation = [
    {
        'role': 'system',
        'content': 'You are Grammar, an AI assistant that helps correct the user\'s sentences to be grammatically correct. When the user provides a sentence, you should correct any grammatical errors and provide the corrected sentence.'
    }
]

# Initial assistant message (optional)
initial_message = "Grammar at your service. I can help correct your sentences."

print(f"Assistant: {initial_message}")
speak_text(initial_message)

# Main loop
while True:
    listen_for_wake_word()
    interaction_counter += 1
    readyToWork = activate_assistant()
    speak_text(readyToWork)
    print(readyToWork)

    # Record user input
    filename = "input.wav"
    record_audio(filename)

    # Transcribe audio to text
    text = transcribe_audio_to_text(filename)
    if text:
        print(f"You said: {text}")
        append_to_log(f"You: {text}\n")

        # Check if the user wants to end the conversation
        if 'thank' in text.lower() or 'bye' in text.lower():
            farewell_message = "You're welcome! Goodbye!"
            print(f"Assistant: {farewell_message}")
            speak_text(farewell_message)
            append_to_log(f"Grammar: {farewell_message}\n")
            break  # Exit the main loop to end the program

        # Generate response using ChatGPT
        conversation.append({'role': 'user', 'content': text})
        conversation = ChatGPT_conversation(conversation)
        assistant_reply = conversation[-1]['content']
        print(f"Assistant: {assistant_reply}")
        append_to_log(f"Grammar: {assistant_reply}\n")

        # Speak the assistant's reply
        speak_text(assistant_reply)
    else:
        print("No speech detected, please try again.")
