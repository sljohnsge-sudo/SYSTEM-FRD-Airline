import urllib.request
import urllib.parse
import json
import base64

class TravelportService:
    def __init__(self):
        self.username = "TP92841090"
        self.password = "o$TC@[M$zi0*AY{y"
        self.client_id = "JUosF2AhzeeW6n2XFTb3iqBc93uOMsk0"
        self.client_secret = "BRhqfMtlfzEnpoBr0tKcBS-ibJPX0ZuwQvz3imXAvKhR1QcsPmzALeJcjtYfsZ69"
        self.access_group = "8F3170D6-487F-46B2-8CEE-B3A200FE931F"
        self.pcc = "7F3C"
        
        self.auth_url = "https://auth.pp.travelport.net/oauth/token"
        self.base_url = "https://api.pp.travelport.net"
        self.token = None

    def get_token(self):
        if self.token:
            return self.token
            
        auth_str = f"{self.client_id}:{self.client_secret}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        
        data = urllib.parse.urlencode({
            'grant_type': 'password',
            'username': self.username,
            'password': self.password
        }).encode('utf-8')
        
        req = urllib.request.Request(
            self.auth_url,
            data=data,
            headers={
                'Authorization': f'Basic {encoded_auth}',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                res = json.loads(response.read().decode())
                self.token = res.get('access_token')
                return self.token
        except Exception as e:
            print("Travelport Auth Failed:", e)
            return None

    def _make_request(self, endpoint, payload=None, method='POST', version='11'):
        token = self.get_token()
        if not token:
            return {"success": False, "error": "Authentication failed with Travelport API."}
            
        headers = {
            'Authorization': f'Bearer {token}',
            'XAUTH_TRAVELPORT_ACCESSGROUP': self.access_group,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'taxBreakDown': 'true'
        }
        
        url = f"{self.base_url}{endpoint}"
        
        data_bytes = json.dumps(payload).encode('utf-8') if payload else None
        
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers=headers,
            method=method
        )
        
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                raw_data = response.read()
                if raw_data.startswith(b'\x1f\x8b'):
                    import gzip
                    res_body = gzip.decompress(raw_data).decode('utf-8', errors='replace')
                else:
                    res_body = raw_data.decode('utf-8', errors='replace')
                return {"success": True, "data": json.loads(res_body) if res_body else {}}
        except Exception as e:
            error_details = str(e)
            if hasattr(e, 'read'):
                try:
                    import gzip
                    raw_data = e.read()
                    if raw_data.startswith(b'\x1f\x8b'):
                        error_details = gzip.decompress(raw_data).decode('utf-8', errors='replace')
                    else:
                        error_details = raw_data.decode('utf-8', errors='replace')
                except Exception as decode_err:
                    error_details = f"Could not decode error response: {decode_err}"
            print(f"Travelport API Failed for {endpoint}:", error_details)
            return {"success": False, "error": f"API request failed: {error_details}"}

    def search_locations(self, keyword):
        # Reference Data API for locations
        endpoint = f"/11/air/reference-data/locations?keyword={urllib.parse.quote(keyword)}&subType=CITY,AIRPORT"
        return self._make_request(endpoint, method='GET')

    def search_hotels(self, city_code):
        # Hotel Search API
        endpoint = "/12/hotel/search"
        payload = {
            "HotelSearchModifiers": {
                "City": city_code
            }
        }
        return self._make_request(endpoint, payload=payload, version='12')

    def search_flights(self, origin, destination, date, adults=1):
        endpoint = "/11/air/catalog/search/catalogproductofferings"
        payload = {
            "CatalogProductOfferingsQueryRequest": {
                "CatalogProductOfferingsRequest": {
                    "@type": "CatalogProductOfferingsRequestAir",
                    "offersPerPage": 20,
                    "maxNumberOfUpsellsToReturn": 4,
                    "contentSourceList": [
                        "GDS"
                    ],
                    "PassengerCriteria": [
                        {
                            "@type": "PassengerCriteria",
                            "number": int(adults),
                            "passengerTypeCode": "ADT"
                        }
                    ],
                    "SearchCriteriaFlight": [
                        {
                            "@type": "SearchCriteriaFlight",
                            "departureDate": date,
                            "From": {
                                "value": origin
                            },
                            "To": {
                                "value": destination
                            }
                        }
                    ]
                }
            }
        }
        return self._make_request(endpoint, payload=payload)

    def book_flight(self, flight_id, passengers, offer_identifier=None):
        if not offer_identifier:
            offer_identifier = "o1"  # Fallback for old cached flights
            
        transaction_id = offer_identifier
        offer_ref = "o1"
        product_ref = "p0"
        parts = offer_identifier.split("::")
        if len(parts) >= 3:
            transaction_id, offer_ref, product_ref = parts[0], parts[1], parts[2]
        elif len(parts) == 2:
            transaction_id, offer_ref = parts[0], parts[1]

        # Step 1: Create Reservation Workbench
        wb_res = self._make_request('/11/air/book/session/reservationworkbench', payload={})
        if not wb_res.get("success"):
            return wb_res
            
        try:
            wb_id = wb_res["data"]["ReservationResponse"]["Reservation"]["Identifier"]["value"]
        except Exception:
            return {"success": False, "error": "Failed to initialize Workbench session."}
            
        # Step 2: Add Flight Offer to Workbench
        offer_payload = {
            "OfferQueryBuildFromCatalogProductOfferings": {
                "BuildFromCatalogProductOfferingsRequest": {
                    "@type": "BuildFromCatalogProductOfferingsRequestAir",
                    "CatalogProductOfferingsIdentifier": {
                        "Identifier": {
                            "value": transaction_id
                        }
                    },
                    "CatalogProductOfferingSelection": [
                        {
                            "@type": "CatalogProductOfferingSelection",
                            "CatalogProductOfferingIdentifier": {
                                "Identifier": {
                                    "value": offer_ref
                                }
                            },
                            "ProductIdentifier": [
                                {
                                    "Identifier": {
                                        "value": product_ref
                                    }
                                }
                            ]
                        }
                    ],
                    "PassengerCriteria": [
                        {
                            "@type": "PassengerCriteria",
                            "number": len(passengers) if passengers else 1,
                            "passengerTypeCode": "ADT"
                        }
                    ]
                }
            }
        }
        
        offer_res = self._make_request(f'/11/air/book/airoffer/reservationworkbench/{wb_id}/offers/buildfromcatalogproductofferings', payload=offer_payload)
        
        # Step 3: Add Passengers to Workbench
        travelers = []
        for i, pax in enumerate(passengers):
            # Try to map generic passenger data to Travelport NDC Schema
            traveler_obj = {
                "@type": "Traveler",
                "passengerTypeCode": "ADT", # Defaulting to ADT for simplicity
                "PersonName": {
                    "@type": "PersonNameDetail",
                    "Prefix": pax.get('title', 'Mr'),
                    "Given": pax.get('first_name', 'Px'),
                    "Surname": pax.get('last_name', 'One')
                },
                "Telephone": [
                    {
                        "@type": "Telephone",
                        "countryAccessCode": "1",
                        "areaCityCode": "909",
                        "phoneNumber": "212456121",
                        "id": str(i+1),
                        "role": "Home"
                    }
                ]
            }
            travelers.append(traveler_obj)
            
        pax_payload = {
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
    def retrieve_pnr(self, pnr_reference):
        # Hit the actual Travelport API to retrieve the reservation
        endpoint = f"/11/air/book/reservation/reservations/{pnr_reference}"
        res = self._make_request(endpoint, method='GET')
        
        if not res.get("success"):
            return {
                "success": False,
                "error": res.get("error", "Failed to retrieve PNR from Travelport.")
            }
            
        data = res.get("data", {})
        
        return {
            "success": True,
            "data": data,
            "Message": f"Successfully retrieved live GDS status for {pnr_reference}"
        }
            
    def issue_ticket(self, pnr_reference):
        endpoint = "/11/air/ticketing"
        payload = {
            "TicketingRequest": {
                "PseudoCityCode": self.pcc,
                "PNR": pnr_reference
            }
        }
        res = self._make_request(endpoint, payload=payload)
        
        # If sandbox fails, return the error so the UI handles it
        if not res.get("success"):
            return {
                "success": False,
                "error": res.get("error", "Ticketing failed via Travelport Sandbox.")
            }
            
        return {
            "success": True,
            "ticket_number": res.get("data", {}).get("TicketNumber", "UnknownTicketNumber"),
            "data": res.get("data")
        }
