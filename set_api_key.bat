@echo off
echo Setting up Gemini API Key...
echo.
echo Please paste your Gemini API key when prompted.
echo (You can get it from: https://makersuite.google.com/app/apikey)
echo.
set /p GEMINI_KEY="Enter your Gemini API key: "

echo.
echo Setting environment variable...
setx GEMINI_API_KEY "%GEMINI_KEY%"

echo.
echo ✓ API key has been set successfully!
echo ✓ You may need to restart your command prompt for the changes to take effect.
echo.
pause
