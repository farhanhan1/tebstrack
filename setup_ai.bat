@echo off
echo =================================
echo TeBSTrack AI Setup
echo =================================
echo.
echo This script will help you set up the OpenAI API key for TeBSTrack AI features.
echo.
echo 1. Get your OpenAI API key from: https://platform.openai.com/account/api-keys
echo 2. Copy the API key (starts with sk-...)
echo 3. Enter it below when prompted
echo.

set /p OPENAI_KEY="Enter your OpenAI API key: "

if "%OPENAI_KEY%"=="" (
    echo Error: No API key provided
    pause
    exit /b 1
)

echo.
echo Setting OpenAI API key as environment variable...

REM Set for current session
set OPENAI_API_KEY=%OPENAI_KEY%

REM Set permanently for user
setx OPENAI_API_KEY "%OPENAI_KEY%"

echo.
echo =================================
echo ✅ OpenAI API key configured!
echo =================================
echo.
echo The API key has been set for:
echo - Current session: ✅
echo - Future sessions: ✅
echo.
echo You can now:
echo 1. Start TeBSTrack: python run.py
echo 2. Use AI categorization
echo 3. Chat with AI assistant
echo 4. Generate email templates
echo.
echo Note: Restart your terminal/VS Code for permanent changes to take effect.
echo.
pause
