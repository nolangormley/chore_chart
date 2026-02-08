@echo off
echo ===================================================
echo CHORE CHART SERVER
echo ===================================================
echo.
echo Your IP Address(es) for Home Access:
ipconfig | findstr "IPv4"
echo.
echo ---------------------------------------------------
echo 1. On this computer, go to: http://localhost:5000
echo 2. On your phone, go to: http://<YOUR_IP>:5000
echo    (Replace <YOUR_IP> with the numbers shown above)
echo ---------------------------------------------------
echo.
python app.py
pause
