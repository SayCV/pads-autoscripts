@echo off
echo,
echo,=====
echo,SPDX-License-Identifier: (GPL-2.0+ OR MIT):
echo,
echo,!!! THIS IS NOT GUARANTEED TO WORK !!!
echo,
echo,Copyright (c) 2023, SayCV
echo,=====
echo,
@echo off&setLocal EnableDelayedExpansion

cd /d "%~dp0"
set "TOPDIR=%cd:\=/%"
title "%~n0"

if not exist .condaenv.cmd echo set condaenv=envSayCV>.condaenv.cmd
call .condaenv.cmd

if not "x%condaenv%" == "x" call activate %condaenv%
if not "%errorlevel%" == "0" echo ::Please preset condaenv in .condaenvrc then run again && goto :eof_with_pause

call pip install -e . 2>&1 | tee %~n0.log

if "%errorlevel%" == "0" goto :eof_with_exit
:eof_with_pause
pause
:eof_with_exit
goto :eof
