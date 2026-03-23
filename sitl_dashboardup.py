import time
import sys
import os
import csv
import json # <--- New import for reading the scenario file
from datetime import datetime
from pymavlink import mavutil

# --- COLORS ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

CONNECTION_STRING = 'udp:127.0.0.1:14552'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def connect_to_sitl():
    print(f"{Colors.BLUE}--- Connecting to SITL on {CONNECTION_STRING} ---{Colors.ENDC}")
    connection = mavutil.mavlink_connection(CONNECTION_STRING)
    connection.wait_heartbeat()
    print(f"{Colors.GREEN}✅ Connected to System {connection.target_system} (Component {connection.target_component}){Colors.ENDC}")
    connection.mav.request_data_stream_send(
        connection.target_system, connection.target_component,
        mavutil.mavlink.MAV_DATA_STREAM_ALL, 4, 1
    )
    return connection

def set_param(connection, param_name, value):
    connection.mav.param_set_send(
        connection.target_system, 1,
        param_name.encode('utf-8'), float(value),
        mavutil.mavlink.MAV_PARAM_TYPE_REAL32
    )
    time.sleep(0.5)

def send_command(connection, command_id, p1=0, p2=0, p3=0, p4=0, p5=0, p6=0, p7=0):
    connection.mav.command_long_send(
        connection.target_system, connection.target_component,
        command_id, 0,
        p1, p2, p3, p4, p5, p6, p7
    )

def pre_flight_checks(connection):
    print(f"\n{Colors.HEADER}🔍 RUNNING PRE-FLIGHT DIAGNOSTICS...{Colors.ENDC}")
    msg = connection.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=1)
    if msg and msg.relative_alt > 1000:
        print(f"[{Colors.FAIL}FAIL{Colors.ENDC}] Drone is ALREADY FLYING!")
        return False
    print(f"{Colors.GREEN}>> ALL SYSTEMS GO. Ready for Launch.{Colors.ENDC}")
    return True

def auto_launch_smart(connection):
    if not pre_flight_checks(connection):
        return
    print(f"\n{Colors.BLUE}[ACTION] Arming & Taking Off...{Colors.ENDC}")
    connection.mav.set_mode_send(connection.target_system, mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, 4)
    send_command(connection, 400, 1) # Arm
    time.sleep(1)
    send_command(connection, 22, 0, 0, 0, 0, 0, 0, 20) # Takeoff
    print(f"{Colors.GREEN}>> Launch Sequence Initiated. 🚀{Colors.ENDC}")

def move_drone_manual(connection):
    print(f"\n{Colors.CYAN}🕹️  MANUAL NAVIGATION (METERS){Colors.ENDC}")
    direction = input(f"{Colors.BOLD}Enter Direction (N/S/E/W/U/D): {Colors.ENDC}").upper()
    try:
        dist = float(input(f"{Colors.BOLD}Enter Distance (meters): {Colors.ENDC}"))
    except: return

    x, y, z = 0, 0, 0
    if direction == 'N': x = dist
    elif direction == 'S': x = -dist
    elif direction == 'E': y = dist
    elif direction == 'W': y = -dist
    elif direction == 'U': z = -dist 
    elif direction == 'D': z = dist
    
    print(f"{Colors.WARNING}>> Moving...{Colors.ENDC}")
    connection.mav.set_position_target_local_ned_send(
        0, connection.target_system, connection.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED,
        0b110111111000, x, y, z, 0, 0, 0, 0, 0, 0, 0, 0)

def fly_to_coords(connection):
    print(f"\n{Colors.CYAN}🌍  FLY TO GLOBAL COORDINATES{Colors.ENDC}")
    try:
        lat = float(input(f"{Colors.BOLD}Enter Latitude (e.g., -35.363261): {Colors.ENDC}"))
        lon = float(input(f"{Colors.BOLD}Enter Longitude (e.g., 149.165230): {Colors.ENDC}"))
        alt = float(input(f"{Colors.BOLD}Enter Altitude (meters): {Colors.ENDC}"))
    except ValueError:
        print(f"{Colors.FAIL}Invalid input!{Colors.ENDC}")
        return

    print(f"{Colors.WARNING}>> Flying to Lat:{lat}, Lon:{lon}, Alt:{alt}m...{Colors.ENDC}")
    
    connection.mav.set_position_target_global_int_send(
        0, connection.target_system, connection.target_component,
        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
        0b110111111000, 
        int(lat * 1e7), 
        int(lon * 1e7), 
        alt,            
        0, 0, 0, 0, 0, 0, 0, 0)

def land_and_stop(connection):
    print(f"\n{Colors.FAIL}🛑  INITIATING LANDING SEQUENCE...{Colors.ENDC}")
    send_command(connection, 21, 0, 0, 0, 0, 0, 0, 0)
    print(f"{Colors.WARNING}>> Drone is Landing... waiting for touch down.{Colors.ENDC}")
    
    while True:
        msg = connection.recv_match(type='HEARTBEAT', blocking=True)
        if msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED == 0:
            print(f"{Colors.GREEN}>> MOTORS DISARMED. Safe to approach.{Colors.ENDC}")
            break
        time.sleep(1)

def scenario_death_test(connection):
    print(f"\n{Colors.FAIL}🚨 RUNNING 'DEATH TEST' SCENARIO 🚨{Colors.ENDC}")
    auto_launch_smart(connection)
    print("   Climbing...", end='')
    time.sleep(10)
    print(" DONE.")
    print(f"{Colors.WARNING}Injecting Failures...{Colors.ENDC}")
    set_param(connection, 'SIM_WIND_SPD', 20.0)
    set_param(connection, 'SIM_GPS_DISABLE', 1.0)
    print(f"{Colors.BOLD}>> TEST COMPLETE.{Colors.ENDC}")

# --- NEW: AUTOMATED SCENARIO RUNNER ---
def run_automated_scenario(connection, filepath):
    print(f"\n{Colors.HEADER}🚀 LOADING AUTOMATED SCENARIO: {filepath}{Colors.ENDC}")
    try:
        with open(filepath, 'r') as file:
            scenario = json.load(file)
    except Exception as e:
        print(f"{Colors.FAIL}Failed to load scenario: {e}{Colors.ENDC}")
        return

    for step in scenario:
        action = step.get("action")
        print(f"\n{Colors.CYAN}[EXECUTING STEP] -> {action}{Colors.ENDC}")
        
        if action == "takeoff":
            auto_launch_smart(connection)
        
        elif action == "delay":
            t = step.get("time", 5)
            print(f"Waiting for {t} seconds...")
            time.sleep(t)
        
        elif action == "inject_wind":
            speed = step.get("speed", 15.0)
            print(f"{Colors.WARNING}Injecting {speed}m/s wind...{Colors.ENDC}")
            set_param(connection, 'SIM_WIND_SPD', speed)
        
        elif action == "gps_fail":
            enable = step.get("enable", 1.0)
            status = "FAILING GPS" if enable == 1.0 else "RESTORING GPS"
            print(f"{Colors.FAIL}{status}...{Colors.ENDC}")
            set_param(connection, 'SIM_GPS_DISABLE', enable)
            
        elif action == "land":
            land_and_stop(connection)
            
    print(f"\n{Colors.GREEN}✅ AUTOMATED SCENARIO COMPLETE.{Colors.ENDC}")

def main():
    clear_screen()
    try:
        conn = connect_to_sitl()
    except Exception as e:
        print(f"Error: {e}")
        return

    while True:
        print("\n" + "="*60)
        print(f"{Colors.BOLD}{Colors.HEADER} 🚁  CHAOS ENGINEER: COMMANDER (v8.0)  {Colors.ENDC}{Colors.ENDC}")
        print("="*60)
        print(f"1. {Colors.GREEN}🛡️   Smart Launch (Takeoff 20m){Colors.ENDC}")
        print(f"2. {Colors.WARNING}🌪️   Inject High Wind{Colors.ENDC}")
        print(f"3. {Colors.FAIL}🚫   Inject GPS Failure{Colors.ENDC}")
        print(f"4. {Colors.BLUE}✅   Reset Normal{Colors.ENDC}")
        print(f"5. {Colors.FAIL}💀   Run 'Death Test' Scenario{Colors.ENDC}")
        print(f"6. {Colors.WARNING}🕹️   Move (Meters - N/S/E/W){Colors.ENDC}")
        print(f"7. {Colors.CYAN}🌍   Fly to Coordinates (Lat/Lon){Colors.ENDC}")
        print(f"8. {Colors.FAIL}🛑   Land & Turn Off (Stop){Colors.ENDC}")
        print(f"9. Exit")
        print(f"10. {Colors.HEADER}🤖  Run Automated JSON Scenario{Colors.ENDC}") # <--- Option 10 added
        
        choice = input(f"\n{Colors.BOLD}Select Mission:{Colors.ENDC} ")

        if choice == '1': auto_launch_smart(conn)
        elif choice == '2': set_param(conn, 'SIM_WIND_SPD', 15.0)
        elif choice == '3': set_param(conn, 'SIM_GPS_DISABLE', 1.0)
        elif choice == '4':
            set_param(conn, 'SIM_WIND_SPD', 0.0)
            set_param(conn, 'SIM_GPS_DISABLE', 0.0)
            print(">> Reset Done.")
        elif choice == '5': scenario_death_test(conn)
        elif choice == '6': move_drone_manual(conn)
        elif choice == '7': fly_to_coords(conn)
        elif choice == '8': land_and_stop(conn)
        elif choice == '9': break
        elif choice == '10': # <--- Option 10 logic added
            filename = input(f"Enter scenario filename (e.g., death_test.json): ")
            run_automated_scenario(conn, filename)

if __name__ == "__main__":
    main()
