
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
    }
}
