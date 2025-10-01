@echo off
echo ================================
echo    GEMINI API KEY SETUP
echo ================================
echo.
echo 1. Go to: https://makersuite.google.com/app/apikey
echo 2. Sign in with your Google account
echo 3. Click "Create API Key"
echo 4. Copy the API key (starts with AIza...)
echo.
echo Then come back here and follow the instructions below:
echo.
echo STEP 1: Press Win+R, type "sysdm.cpl" and press Enter
echo STEP 2: Click "Environment Variables" button
echo STEP 3: Under "User variables", click "New"
echo STEP 4: Variable name: GEMINI_API_KEY
echo STEP 5: Variable value: [paste your API key here]
echo STEP 6: Click OK, OK, OK
echo.
echo OR use the command below in a NEW command prompt:
echo.
echo setx GEMINI_API_KEY "YOUR_API_KEY_HERE"
echo.
echo (Replace YOUR_API_KEY_HERE with your actual key)
echo.
pause

