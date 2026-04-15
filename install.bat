@echo off
echo =========================================
echo   AQUA VITA - SPA Management System
echo   Инсталационен скрипт
echo =========================================
echo.

echo [1/3] Инсталиране на Python зависимости...
pip install mysql-connector-python bcrypt

echo.
echo [2/3] Готово!
echo.
echo [3/3] ВАЖНО - Следвайте тези стъпки преди да стартирате:
echo.
echo   1. Стартирайте XAMPP Control Panel
echo   2. Стартирайте Apache и MySQL
echo   3. Отворете phpMyAdmin: http://localhost/phpmyadmin
echo   4. Импортирайте файла "database.sql"
echo      (Import -^> Choose File -^> database.sql -^> Go)
echo.
echo   5. Стартирайте приложението:
echo      python main.py
echo.
echo =========================================
echo   Данни за вход по подразбиране:
echo   Потребителско ime: admin
echo   Парола:            admin123
echo =========================================
pause
