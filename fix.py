with open(r'd:\GS\SYSTEM-FRD-Airline\services\travelport_service.py', 'r', encoding='utf-8') as f:
    text = f.read()

prefix = text.split('        pax_payload = {')[0]
suffix = '    def retrieve_pnr(self, pnr_reference):' + text.split('    def retrieve_pnr(self, pnr_reference):')[1]

new_mid = '''        pax_payload = {
            "TravelerListRequest": {
                "@type": "TravelerListRequest",
                "Traveler": travelers
            }
        }
        
        pax_res = self._make_request(f'/11/air/book/traveler/reservationworkbench/{wb_id}/travelers/list', payload=pax_payload)
        
        # Step 4: Handle the API response and Commit
        if not offer_res.get("success"):
            return offer_res
            
        if "Result" in offer_res.get("data", {}).get("OfferListResponse", {}):
            result = offer_res["data"]["OfferListResponse"]["Result"]
            if "Error" in result:
                return {"success": False, "error": f"Offer Data Invalid: {result['Error']}"}
                
        # Attempt to get the real PNR by committing the workbench
        commit_payload = {
            "ReservationQueryCommitReservation": {
                "@type": "ReservationQueryCommitReservation",
                "ReceivedFrom": "SYSTEM-FRD-AGENT",
                "enableTwoStepCommitInd": True,
                "overrideMCTInd": False,
                "errorWhenScheduleChangesInd": True,
                "errorWhenOfferPriceChangesInd": True
            }
        }
        commit_res = self._make_request(f'/11/air/book/reservation/reservations/{wb_id}', payload=commit_payload)
        
        pnr = None
        if commit_res.get("success"):
            try:
                res_obj = commit_res.get("data", {}).get("ReservationResponse", {}).get("Reservation", {})
                receipts = res_obj.get("Receipt", [])
                for receipt in receipts:
                    conf = receipt.get("Confirmation", {})
                    if "Locator" in conf:
                        pnr = conf["Locator"]["value"]
                        break
            except Exception:
                pass
                
        if not pnr:
            # Try to grab the error message from the commit response
            err_msg = "Unknown Commit Error"
            try:
                res_obj = commit_res.get("data", {}).get("ReservationResponse", {}).get("Result", {})
                if "Error" in res_obj and len(res_obj["Error"]) > 0:
                    err_msg = res_obj["Error"][0].get("Message", err_msg)
            except Exception:
                pass
            return {"success": False, "error": f"Failed to generate PNR. API Error: {err_msg}"}
        
        return {
            "success": True,
            "data": {
                "ReservationBuildResponse": {
                    "PNR": pnr,
                    "Status": "Confirmed",
                    "FlightId": flight_id,
                    "WorkbenchId": wb_id,
                    "PassengersBooked": len(passengers)
                }
            }
        }
'''

with open(r'd:\GS\SYSTEM-FRD-Airline\services\travelport_service.py', 'w', encoding='utf-8') as f:
    f.write(prefix + new_mid + suffix)
