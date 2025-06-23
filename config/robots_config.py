
robots_config = {
    "Scara": {
        "type": "ScaraRobot",
        "ip": "192.168.3.104",
        "port": 3920,
        "program_name": "ScaraReal.xml",
        "sequence_path": "sequences/Scara/",
        "id": "scara",
        "var_file": "VariableScaraReal.xml"
    },
    "RebelLine": {
        "type": "RebelLineRobot",
        "ip": "192.168.3.101",
        "port": 3920,
        "program_name": None,
        "sequence_path": "sequences/RebelLine/",
        "id": "rebelline",
        "var_file": "VariableRebelLine.xml"
    },
    "Rebel1": {
        "type": "Rebel1Robot",
        "ip": "192.168.3.102",
        "port": 3920,
        "program_name": "Rebel1.xml",
        "sequence_path": "sequences/Rebel1/",
        "id": "rebel1",
        "var_file": "VariableRebel1.xml"
    },
    "Rebel2": {
        "type": "Rebel2Robot",
        "ip": "192.168.3.103",
        "port": 3920,
        "program_name": "Rebel2.xml",
        "sequence_path": "sequences/Rebel2/",
        "id": "rebel2",
        "var_file": "VariableRebel2.xml"
    },
    
    "D1Door": {
        "type": "D1Motor",
        "ip": "192.168.3.70",
        "port": 502,
        "id": "d1door",
        "role": "door",
        "status" : [0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 65, 0, 0, 0, 0, 2],
        "shutdown": [0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 6, 0],
        "switchOn" : [0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 7, 0],
        "enableOperation" : [0, 0, 0, 0, 0, 15, 0, 43,13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 15, 0],
        "stop" : [0, 0, 0, 0, 0, 15, 0, 43,13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 15, 1],
        "reset" : [0, 0, 0, 0, 0, 15, 0, 43, 13, 1, 0, 0, 96, 64, 0, 0, 0, 0, 2, 0, 1],
        "DInputs": [0, 0, 0, 0, 0, 13, 0, 43, 13, 0, 0, 0, 96, 253, 0, 0, 0, 0, 4],
        
    },
        
    # "D1Elevator": {
    #     "type": "D1Motor",
    #     "ip": "192.168.3.71",
    #     "port": 502,
    #     "id": "d1elevator",
    #     "role": "elevator"
    # }
}

