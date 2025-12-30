@echo off
setlocal

set "REPOROOT=%~dp0.."
set "ENVFILE=%REPOROOT%\.env"
set "ENVEXAMPLE=%REPOROOT%\env.example"

if not exist "%ENVFILE%" (
  if exist "%ENVEXAMPLE%" (
    copy /Y "%ENVEXAMPLE%" "%ENVFILE%" >nul
  ) else (
    type nul > "%ENVFILE%"
  )
)

notepad "%ENVFILE%"
