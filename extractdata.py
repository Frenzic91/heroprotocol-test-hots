import json

def extract_data(replayfile):
    # simulated game state variables
    player_death_counts = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    player_death_times = [[], [], [], [], [], [], [], [], [], [], [], []]
    footmans = []
    player_minion_xp = {} # maps player id to xp gained from killing minions
    current_wave_number = 0
    last_used_gameloop = 0
    live_minions = {} # maps m_tag of minion to tuple (m_unitTypeName, corresponding_wave_num)
    unit_type_to_xp = {"FootmanMinion": (70, 1.2), "WizardMinion": (62.4, 1.8), "RangedMinion": (60, 2.0)} # maps m_unitTypeName to tuple (base minion xp, xp scaling factor)
    
    potential_team_xp = {"team_1": 0, "team_2": 0}
    earned_team_xp = {"team_1": 0, "team_2": 0}
    
    player_information = {1: {}, 2: {}, 3: {}, 4: {}, 5: {}, 6: {}, 7: {}, 8: {}, 9: {}, 10: {}}
    
    # update game state based on data in output file until specified line is reached
    try:
        f = open(replayfile, 'r')
        #json_objects_processed = 0
        line_num = 0
        start_of_next_json = ''
        while True:
            json_string = start_of_next_json
            cur_line = f.readline().replace("None", "-1")
            line_num += 1
            #print line_num
            json_string += cur_line 
            while True:
                cur_line = f.readline().replace("None", "-1")
                line_num += 1
                #print line_num
                if cur_line[0] != '{':
                    json_string += cur_line
                else:
                    start_of_next_json = cur_line
                    break
                
            #json_objects_processed += 1
            #print json_objects_processed
        
            json_string_replaced = json_string.replace("'", "\"")
            #print json_string_replaced
        
            json_object = json.JSONDecoder().decode(json_string_replaced)
            
            if json_object["_event"] == "NNet.Replay.Tracker.SStatGameEvent" and "m_eventName" in json_object.keys() and json_object["m_eventName"] == "PlayerSpawned":
                if "m_stringData" in json_object.keys() and json_object["m_stringData"][0]["m_key"] == "Hero":
                    player_id = json_object["m_intData"][0]["m_value"]
                    player_information[player_id]["hero_name"] = json_object["m_stringData"][0]["m_value"]

            if "m_eventName" in json_object.keys() and json_object["m_eventName"] == "PlayerDeath":
                player_id = json_object["m_intData"][0]["m_value"]
                player_death_counts[player_id] += 1
                
                player_death_time = json_object["_gameloop"] / 16.0
                player_death_times[player_id].append(player_death_time)
            
            #if "_event" in json_object.keys() and json_object["_event"] == "NNet.Replay.Tracker.SUnitBornEvent":
            #    footmans.append((json_object["m_unitTagIndex"], json_object["m_unitTagRecycle"], json_object["m_unitTypeName"]))
              
            if "_event" in json_object.keys() and json_object["_event"] == "NNet.Replay.Tracker.SUnitBornEvent" and json_object["m_unitTypeName"] in unit_type_to_xp.keys():
                if json_object["_gameloop"] > (last_used_gameloop + 100):
                    last_used_gameloop = json_object["_gameloop"]
                    current_wave_number += 1
                m_tag = (json_object["m_unitTagIndex"] << 18) + json_object["m_unitTagRecycle"]
                live_minions[m_tag] = (json_object["m_unitTypeName"], current_wave_number)
                
            if "_event" in json_object.keys() and json_object["_event"] == "NNet.Replay.Tracker.SUnitDiedEvent":
                m_tag = (json_object["m_unitTagIndex"] << 18) + json_object["m_unitTagRecycle"]
                if m_tag in live_minions:
                    m_unitTypeName = live_minions[m_tag][0]
                    corresponding_wave_num = live_minions[m_tag][1]
                    
                    minion_base_xp = unit_type_to_xp[m_unitTypeName][0]
                    minion_scaling_factor = unit_type_to_xp[m_unitTypeName][1]
                    
                    player_id = json_object["m_killerPlayerId"]
                    xp_from_kill = minion_base_xp + ((corresponding_wave_num / 2) * minion_scaling_factor)
                    
                    if json_object["m_killerPlayerId"] in [1, 2, 3, 4, 5, 11]:
                        potential_team_xp["team_1"] += xp_from_kill
                    else:
                        potential_team_xp["team_2"] += xp_from_kill
                    
                    if player_id in player_minion_xp:
                        player_minion_xp[player_id] += xp_from_kill
                    else:
                        player_minion_xp[player_id] = xp_from_kill
               
                    del live_minions[m_tag]
                    
            if ("_event" in json_object.keys()) and (json_object["_event"] == "NNet.Replay.Tracker.SStatGameEvent") and (json_object["m_eventName"] == "EndOfGameXPBreakdown"):
                if json_object["m_intData"][0]["m_value"] == 1:
                    earned_team_xp["team_1"] = (json_object["m_fixedData"][0]["m_value"] / 4096)
                elif json_object["m_intData"][0]["m_value"] == 6: 
                    earned_team_xp["team_2"] = (json_object["m_fixedData"][0]["m_value"] / 4096)
                
            if json_object["_event"] == "NNet.Replay.Tracker.SStatGameEvent" and "m_eventName" in json_object.keys() and json_object["m_eventName"] == "PlayerDeath":
                player_id = json_object["m_intData"][0]["m_value"]
                if "death_count" in player_information[player_id].keys():
                    player_information[player_id]["death_count"] += 1
                else:
                    player_information[player_id]["death_count"] = 1
                
            if json_object["_event"] == "NNet.Replay.Tracker.SStatGameEvent" and "m_eventName" in json_object.keys() and json_object["m_eventName"] == "EndOfGameTimeSpentDead":
                player_id = json_object["m_intData"][0]["m_value"]
                player_information[player_id]["death_time"] = json_object["m_fixedData"][0]["m_value"] / 4096

    except:
        print live_minions
        print current_wave_number
        print player_minion_xp
        print "------"
        print potential_team_xp
        print earned_team_xp
        print player_information
        print "------"
        print "Team 1 soaked " + str(int(round(earned_team_xp["team_1"] / potential_team_xp["team_1"], 2) * 100)) + "% of available XP from minions" 
        print "Team 2 soaked " + str(int(round(earned_team_xp["team_2"] / potential_team_xp["team_2"], 2) * 100)) + "% of available XP from minions"
        print "------"
        
        for player_id in player_information:
            if "death_count" in player_information[player_id]:
                print player_information[player_id]["hero_name"] + " had an average death time of " + str(round(player_information[player_id]["death_time"] / player_information[player_id]["death_count"])) + " with " + str(player_information[player_id]["death_count"]) + " death(s)." + " Total time dead was " + str(player_information[player_id]["death_time"]) + " seconds."
        
        #print footmans
        
        #print json_object["_bits"]
        #print json_object["_event"]
        #print json_object["_eventid"]
        #print json_object["_gameloop"]
        #print json_object["m_playerId"]
        #print json_object["m_slotId"]
        #print json_object["m_type"]
        #print json_object["m_userId"]        
        
        #print player_death_counts
        #print player_death_times
    
        
        # 3:42, 5:14, 6:44, 10:01, 11:33, 12:39, 14:20, 15:56
    
    #(unitTagIndex << 18) + unitTagRecycle
    #print (112 << 18) + 30
    #print (115 << 18) + 16
    
    #96, 2
    #93, 2
    #132, 2
    #149, 2
    #88, 2
    #84, 2 
    