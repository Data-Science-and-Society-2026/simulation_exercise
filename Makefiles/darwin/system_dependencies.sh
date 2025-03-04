#!/bin/sh


echo "Installing Homebrew if missing..."
if ! which brew > /dev/null ; then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo 'eval $(brew shellenv)' >> ~/.zprofile
    source ~/.zprofile
fi

echo >> ~/.bash_profile # adding to path
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.bash_profile
eval "$(/opt/homebrew/bin/brew shellenv)"

echo "Updating homebrew..."
brew update && brew upgrade

echo "Installing packages"
brew install uv
brew install git # if missing 
