## FEATURE :

1. Multi accounts

2. Multi servers

3. Gemini AI ( ON / OFF )

5. Auto detecd Slow mode Server Chat ( ON / OFF )

6. Auto Delete Message with Delay ( ON / OFF ). & Auto Delete message after send

7. Auto Reply Message

8. Auto send message with file `tersuratkan.txt`

9. Auto read new chat in server


###Git clone 
```
git clone https://github.com/19seniman/send-message-to-discord.git
cd send-message-to-discord
python3 -m venv send-message-to-discord
source send-message-to-discord/bin/activate
pip3 install -r requirements.txt
```
Edit file `.env` copy & paste your Gemini API & Discord token :
```
nano .env
```
Run Scrpt
```
python3 chat.py
```


# Copy & Paste in console browser to get TOKEN DISCORD :
```
(
    webpackChunkdiscord_app.push(
        [
            [''],
            {},
            e => {
                m=[];
                for(let c in e.c)
                    m.push(e.c[c])
            }
        ]
    ),
    m
).find(
    m => m?.exports?.default?.getToken !== void 0
).exports.default.getToken()
```





