#!/bin/bash

# Streamlit with AWS Profile
export AWS_PROFILE=dit-training

echo "=== Streamlit 起動用スクリプト ==="
echo "AWS_PROFILE: $AWS_PROFILE"
echo "==============================="

# Streamlit実行
streamlit run app.py