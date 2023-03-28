fetch_lock = asyncio.Lock()

async def getData(url):
    #global cache
    async with fetch_lock:
        try:
            print("Fetching: "+url+"?ts="+str(time.time()))
            r = requests.get(url+"?ts="+str(time.time()))
            #print(r.text)
            cache[url] = json.loads(r.text)
            #print(cache)
        except Exception as e:
            print("Failed to load ", url)
            print("Exception: ", e)

def processData(cache):
    #global cache
    output = {}
    for url, data in cache.items():
        output[url] = { 'grill': {}, 'food': {}, 'setpoints':{}, 'status': {}}
        # {'current': {'probe1_temp': 145, 'grill_temp': 247, 'probe2_temp': 141}, 'setpoints': {'probe2': 160, 'grill_notify': 250, 'grill': 250, 'probe1': 0}, 'status': {'units': 'F', 'status': 'active', 'pellets': 'Bear Mountain Hickory', 'name': 'Even Embers', 's_plus': True, 'mode': 'Hold', 'pelletlevel': 100}}
        # {"current":{"F":{"Probe1":0,"Probe2":0,"Probe3":0},"NT":{"Grill":0,"Probe1":0,"Probe2":0,"Probe3":0},"P":{"Grill":0},"PSP":0},"notify_data":[{"keep_warm":false,"label":"Grill","name":"Cabinet","req":false,"shutdown":false,"target":0,"type":"probe"},{"keep_warm":false,"label":"Probe1","name":"Probe-1","req":false,"shutdown":false,"target":0,"type":"probe"},{"keep_warm":false,"label":"Probe2","name":"Probe-2","req":false,"shutdown":false,"target":0,"type":"probe"},{"keep_warm":false,"label":"Probe3","name":"Probe-3","req":false,"shutdown":false,"target":0,"type":"probe"},{"keep_warm":false,"label":"Timer","req":false,"shutdown":false,"type":"timer"},{"keep_warm":false,"label":"Hopper","last_check":0,"req":true,"shutdown":false,"type":"hopper"}],"primary_setpoint":0,"status":{"mode":"Stop","name":"Masterbuilt XL","primary_setpoint":0,"s_plus":true,"status":"","ui_hash":1121140636,"units":"F"}}
        if('F' in data['current']):
            #output[url]['status'] 
            #new version of API (PiFire version>1.3.5)
            food_probes = sorted(data['current']['F'])
            for probe in data['current']['F']:
                output[url]['food'][probe] = str(data['current']['F'][probe])
            #output[url]['food'][probe].sort()
            grill_probes = sorted(data['current']['P'])
            for probe in data['current']['P']:
                output[url]['grill'][probe] = str(data['current']['P'][probe])
            #output[url]['grill'][probe].sort()
            output[url]['setpoints']['Grill'] = str(data['current']['PSP'])
            for probe in data['notify_data']:
                if(probe['type'] == 'probe' and probe['label'] != 'Grill'):
                    output[url]['setpoints'][probe['label']] = str(probe['target'])
                #{'keep_warm': False, 'name': 'Cabinet', 'req': False, 'label': 'Grill', 'target': 0, 'shutdown': False, 'type': 'probe'}
            output[url]['status']['mode'] = data['status']['mode']
            output[url]['status']['s_plus'] = data['status']['s_plus']
            output[url]['status']['name'] = data['status']['name'] if len(data['status']['name']) else 'Grill'
        else:
            #old version of API (PiFire version<=1.3.5)
            output[url]['grill']['Grill'] = str(data['current']['grill_temp'])
            output[url]['food']['Probe1'] = str(data['current']['probe1_temp'])
            output[url]['food']['Probe2'] = str(data['current']['probe2_temp'])
            output[url]['setpoints']['Grill'] = str(data['setpoints']['grill'])
            output[url]['setpoints']['Probe1'] = str(data['setpoints']['probe1'])
            output[url]['setpoints']['Probe2'] = str(data['setpoints']['probe2'])
            output[url]['status']['mode'] = data['status']['mode']
            output[url]['status']['s_plus'] = data['status']['s_plus']
            output[url]['status']['name'] = data['status']['name'] if len(data['status']['name']) else 'Grill'
    return output

async def main():
    grill_data = {}
    y_offset = 0
    per_grill_height = box_height + 16
    while True:
        grill_data = processData(cache)
        grill_offset = 0
        #display.fill(0)
        ts = time.time()
        #update screen every second
        for addr in grill_addresses:
            #fetch data
            if(addr in grill_data):
                if(grill_data[addr]['status']['mode'] != 'Stop' and ts % active_delay == 0):
                    task = asyncio.create_task(getData(addr))
                elif(ts % idle_delay == 0):
                    task = asyncio.create_task(getData(addr))
                # an update exists, display data
                print("Y_offset: "+ str(y_offset))
                if len(grill_data) > 2:
                    y_start = y_offset-grill_offset if y_offset-grill_offset < screen_height else y_offset-grill_offset-(len(grill_data)*per_grill_height)
                elif len(grill_data) > 1:
                    y_start = y_offset-grill_offset if y_offset < grill_offset else y_offset-grill_offset-(len(grill_data)*per_grill_height)
                else:
                    y_start = 10
                if 'name' in grill_data[addr]['status']:
                    print(grill_data[addr]['status'])
                    display.text(grill_data[addr]['status']['name'],round(screen_width/2)-(4*len(grill_data[addr]['status']['name'])),y_start)
                else:
                    display.text("Unavailable",round(screen_width/2)-(4*len("Unavailable")),y_start)
                probe_num = 0
                gutter = int((screen_width-box_spacing*(len(grill_data[addr]['grill'])+len(grill_data[addr]['food'])-1)-box_width*(len(grill_data[addr]['grill'])+len(grill_data[addr]['food'])))/2)
                print(grill_data[addr]['grill'])
                for grill_probe in grill_data[addr]['grill'].values():
                    #print(grill_probe)
                    x_start = gutter+probe_num*box_width+probe_num*box_spacing
                    print("X:"+str(x_start) + ", Y:"+str(y_start))
                    display.rect(x_start,y_start+9,box_width,box_height,1)
                    display.text('G',int(box_width/2)-4+x_start,int(box_height/5)-2+y_start+9)
                    display.fill_rect(x_start+1, int(box_height/5)-2+y_start+18, box_width-2, box_height-15, 0)
                    display.text(grill_probe,int(box_width/2)-(4*len(grill_probe))+x_start,int(3*box_height/5)+y_start+9)
                    probe_num += 1
                print(grill_data[addr]['grill'])
                for food_probe in grill_data[addr]['food'].values():
                    # print(food_probe)
                    x_start = gutter+probe_num*box_width+probe_num*box_spacing
                    print("X:"+str(x_start) + ", Y:"+str(y_start))
                    display.rect(x_start,y_start+9,box_width,box_height,1)
                    display.text('P',int(box_width/2)-4+x_start,int(box_height/5)-2+y_start+9)
                    display.fill_rect(x_start+1, int(box_height/5)-2+y_start+18, box_width-2, box_height-15, 0)
                    display.text(food_probe,int(box_width/2)-(4*len(food_probe))+x_start,int(3*box_height/5)+y_start+9)
                    probe_num += 1
                if len(grill_data) > 1:
                    display.line(2,y_start+11+box_height,screen_width-2,y_start+11+box_height,1)
                grill_offset += per_grill_height
            else:
                task = asyncio.create_task(getData(addr))
        if len(grill_data) > 1:
            display.scroll(0,display_scroll_rate)
            for line in range(0,display_scroll_rate):
                display.line(0,line,screen_width,line,0)
            y_offset += display_scroll_rate
            y_offset = y_offset % (per_grill_height * len(grill_addresses))
        display.show()
        if(ts % 60 == 0):
            print('heartbeat')
            print(grill_data)
            print(ts)
        await asyncio.sleep(1)
asyncio.run(main())