# Messages.app OTP codes - Alfred Workflow


## Description

This workflow allows you to conveniently enter an SMS OTP code that you received on your iPhone.  
For this to work, you have to [enable Message Forwarding](https://support.apple.com/guide/messages/get-sms-texts-from-iphone-on-your-mac-icht8a28bb9a/mac) on your iPhone.

This workflow uses python3 and sqlite3 (both should come with macOS, so no need to install anything via Homebrew).

It reads the latest 20 messages in the Messages.app, filters out the messages without anything that looks like an OTP code and shows it.  
Then, you may select the OTP code, press Enter and it will be pasted to wherever-you-were.


## Install

Download the latest .alfred-workflow file from the Releases section and open it. it should be imported to Alfred.

## Usage

Press a hotkey (`⌘⌥⌃\` by default) or open Alfred and type `otp`. Alfred will list the latest messages containing OTP codes.  
Press Enter on the selected code to paste the code.

To change the hotkey/keyword, edit the blocks in the imported workflow.

## Tweaking

Right click on a "Messages.app OTP" workflow, choose "Open in Finder".  
Open `messages.py` with a text/code editor.

To tweak the filters/amount of the messages that are read from Messages.app, edit the SQL query in the `SQL` variable.  
To tweak the OTP detection, see the variables `OTP_PATTERN`, `OTP_PATTERN_WHITELIST`, `OTP_PATTERN_BLACKLIST`.  
