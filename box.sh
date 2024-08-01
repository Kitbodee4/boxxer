#!/bin/bash

# Update package list
sudo apt-get update

# Install python3-pip
sudo apt-get install -y python3-pip

# Install required Python packages
pip install -r requirements.txt

# Initialize an empty array to store tokens
tokens=()

# Function to prompt user for tokens
prompt_tokens() {
  while true; do
    read -p "Enter a token (or press enter to finish): " token
    if [[ -z "$token" ]]; then
      break
    fi
    tokens+=("$token")
  done
}

# Prompt user for tokens
prompt_tokens

# Write tokens to auths.json
cat <<EOT > auths.json

  [
$(for token in "${tokens[@]}"; do echo "    \"$token\","; done | sed '$ s/,$//')
  ]

EOT

# Create or attach to a screen session named 'boxxer' and run the Python script
screen -S boxxer -dm bash -c 'python3 box.py'


