#! /bin/bash

# cd to current path
dirname=`dirname $0`
tmp="${dirname#?}"
if [ "${dirname%$tmp}" != "/" ]; then
	dirname=$PWD/$dirname
fi
echo $dirname
cd "$dirname"

# close driver if it running
AppName=pentablet
AppDir=pentablet
pid=`ps -e|grep $AppName`
appScript=$AppName".sh"
if [ -n "$pid" ]; then
	echo $pid
	arr=()
	while read -r line; do
	   arr+=("$line")
	done <<< "$pid"
	for val in "${arr[@]}";
	do
		appid=`echo $val | awk '{print $1}'`
	   	name=`echo $val | awk '{print $4}'`
	   	echo "ID:"$appid 
		echo "Name:"$name
		if [ "$name" = "$appRunScript" ]; then
			echo "close $appRunScript"
			kill -15 $appid
		elif [ "$name" = "$AppName" ]; then
			echo "close $AppName"
			kill -15 $appid
		fi
	done
fi

#Copy rule
sysRuleDir="/lib/udev/rules.d"
appRuleDir=./App$sysRuleDir
ruleName="10-xp-pen.rules"

#echo "$appRuleDir/$ruleName"
#echo "$sysRuleDir/$ruleName"

if [ -f $appRuleDir/$ruleName ]; then
	str=`cp $appRuleDir/$ruleName $sysRuleDir/$ruleName`
	if [ "$str" !=  "" ]; then 
		echo "$str";
	fi
else
	echo "Cannot find driver's rules in package"
	exit
fi

#install app
sysAppDir="/usr/lib"
appAppDir=./App$sysAppDir/$AppName
exeShell="pentablet.sh"

#echo $sysAppDir
#echo $appAppDir

if [ -d "$appAppDir" ]; then
	str=`cp -rf $appAppDir $sysAppDir`
	if [ "$str" !=  "" ]; then 
		echo "$str";
	fi
else
	echo "Cannot find driver's files in package"
	exit
fi

#echo "shell path "$sysAppDir/$AppDir/$exeShell
if [ -f $sysAppDir/$AppDir/$exeShell ]; then
	str=`chmod +0755 $sysAppDir/$AppName/$exeShell`
	if [ "$str" !=  "" ]; then 
		echo "Cannot add permission to start script"
		echo "$str";
	fi
else
	echo "can not find start script"
	exit
fi

#echo "exe path "$sysAppDir/$AppDir/$AppName
if [ -f $sysAppDir/$AppDir/$AppName ]; then
	str=`chmod +0555 $sysAppDir/$AppDir/$AppName`
	if [ "$str" !=  "" ]; then 
		echo "Cannot add permission to app"
		echo "$str";
	fi
else
	echo "can not find app"
	exit
fi

# install shortcut
sysDesktopDir=/usr/share/applications
sysAppIconDir=/usr/share/icons
sysAutoStartDir=/etc/xdg/autostart

appDesktopDir=./App$sysDesktopDir
appAppIconDir=./App$sysAppIconDir
appAutoStartDir=./App$sysAutoStartDir

appDesktopName=xp$AppName.desktop
appIconName=$AppName.png


#echo $appDesktopDir/$appDesktopName
#echo $sysDesktopDir/$appDesktopName
#echo $appAppIconDir/$appIconName
#echo $sysAppIconDir/$appIconName

if [ -f $appDesktopDir/$appDesktopName ]; then
	str=`cp $appDesktopDir/$appDesktopName $sysDesktopDir/$appDesktopName`
	if [ "$str" !=  "" ]; then 
		echo "$str"
	fi
else
	echo "Cannot find driver's shortcut in package"
	exit
fi

if [ -f $appAppIconDir/$appIconName ]; then
	str=`cp $appAppIconDir/$appIconName $sysAppIconDir/$appIconName`
	if [ "$str" !=  "" ]; then 
		echo "$str"
	fi
else
	echo "Cannot find driver's icon in package"
	exit
fi


absAppDir=/usr/lib/pentablet
absConfPath=$absAppDir/conf/xppen
absLibPath=$absAppDir/lib
absPlatPath=$absAppDir/platforms


chmod +0777 /etc/xdg/autostart/xppentablet.desktop
chmod +0777 /usr/share/applications/xppentablet.desktop
chmod +0777 /usr/share/icons/pentablet.png

chmod +0777 $absAppDir/pentablet
chmod +0777 $absAppDir/pentablet.sh
chmod +0666 $absAppDir/resource.rcc

chmod +0777 $absConfPath
chmod +0777 $absLibPath
chmod +0777 $absPlatPath

chmod +0666 $absConfPath/config.xml
chmod +0666 $absConfPath/language.ini
chmod +0666 $absConfPath/name_config.ini

chmod +0666 $absLibPath/libicudata.so.56
chmod +0666 $absLibPath/libicui18n.so.56
chmod +0666 $absLibPath/libicuuc.so.56
chmod +0666 $absLibPath/libQt5Core.so.5
chmod +0666 $absLibPath/libQt5DBus.so.5
chmod +0666 $absLibPath/libQt5Gui.so.5
chmod +0666 $absLibPath/libQt5Network.so.5
chmod +0666 $absLibPath/libQt5Widgets.so.5
chmod +0666 $absLibPath/libQt5X11Extras.so.5
chmod +0666 $absLibPath/libQt5XcbQpa.so.5
chmod +0666 $absLibPath/libQt5Xml.so.5

chmod +0666 $absPlatPath/libqxcb.so

lockfile="/tmp/qtsingleapp-Pentab-9c9b-lockfile"
touch $lockfile
chmod +0666 $lockfile


if [ -f "/etc/xdg/autostart/pentablet.desktop" ]; then
	rm /etc/xdg/autostart/ugee-pentablet.desktop
fi


echo "Installation successful!"
echo "If you are installing for the first time, please use it after restart."
