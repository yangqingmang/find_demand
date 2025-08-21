@echo off
echo Starting Vercel deployment...
cd /d "%~dp0"
vercel --prod --yes --force
pause