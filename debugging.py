# from app import create_app, db
# from models import Campaign, Sponsor, AdRequest

# app = create_app()

# with app.app_context():
#     print("Checking all campaigns and their sponsors:")
#     all_campaigns = Campaign.query.all()
#     for campaign in all_campaigns:
#         print(f"Campaign ID: {campaign.id}, Title: {campaign.title}")
#         print(f"Sponsor ID: {campaign.sponsor_id}")
#         if campaign.sponsor:
#             print(f"Sponsor Company: {campaign.sponsor.company_name}")
#         else:
#             print("No sponsor associated")
#         print("---")

#     print("\nChecking all AdRequests and their associated campaigns and sponsors:")
#     all_ad_requests = AdRequest.query.all()
#     for ad_request in all_ad_requests:
#         print(f"AdRequest ID: {ad_request.id}")
#         print(f"Campaign ID: {ad_request.campaign_id}")
#         if ad_request.campaign:
#             print(f"Campaign Title: {ad_request.campaign.title}")
#             print(f"Sponsor ID: {ad_request.campaign.sponsor_id}")
#             if ad_request.campaign.sponsor:
#                 print(f"Sponsor Company: {ad_request.campaign.sponsor.company_name}")
#             else:
#                 print("No sponsor associated with this campaign")
#         else:
#             print("No campaign associated with this AdRequest")
#         print("---")

# from app import create_app, db
# from models import Campaign, Sponsor, AdRequest

# app = create_app()

# with app.app_context():
#     sponsor = Sponsor.query.get(2)
#     if sponsor:
#         print(f"Sponsor found: ID {sponsor.id}, Company {sponsor.company_name}")
#     else:
#         print("No sponsor found with ID 2")

#     # Let's also check all sponsors
#     all_sponsors = Sponsor.query.all()
#     print(f"Total sponsors in database: {len(all_sponsors)}")
#     for s in all_sponsors:
#         print(f"Sponsor ID: {s.id}, Company: {s.company_name}")








# from app import create_app, db
# from models import Campaign, Sponsor, AdRequest

# app = create_app()

# with app.app_context():
#     campaign = Campaign.query.get(1)
#     if campaign:
#         valid_sponsor = Sponsor.query.first()  # Get the first (and only) sponsor
#         if valid_sponsor:
#             campaign.sponsor_id = valid_sponsor.id
#             print(f"Updated campaign sponsor to: {valid_sponsor.company_name}")
#         else:
#             campaign.sponsor_id = None
#             print("No valid sponsors found. Set sponsor_id to None.")
#         db.session.commit()
#     else:
#         print("Campaign not found")

#     # Verify the change
#     campaign = Campaign.query.get(1)
#     if campaign:
#         print(f"Campaign ID: {campaign.id}, Title: {campaign.title}")
#         print(f"Sponsor ID: {campaign.sponsor_id}")
#         if campaign.sponsor:
#             print(f"Sponsor Company: {campaign.sponsor.company_name}")
#         else:
#             print("No sponsor associated")
#     else:
#         print("Campaign not found")



# from app import create_app, db
# from models import Campaign, Sponsor, AdRequest

# app = create_app()

# with app.app_context():
#     print("Checking all campaigns and their sponsors:")
#     all_campaigns = Campaign.query.all()
#     for campaign in all_campaigns:
#         print(f"Campaign ID: {campaign.id}, Title: {campaign.title}")
#         print(f"Sponsor ID: {campaign.sponsor_id}")
#         if campaign.sponsor:
#             print(f"Sponsor Company: {campaign.sponsor.company_name}")
#         else:
#             print("No sponsor associated")
#         print("---")

#     print("\nChecking all AdRequests and their associated campaigns and sponsors:")
#     all_ad_requests = AdRequest.query.all()
#     for ad_request in all_ad_requests:
#         print(f"AdRequest ID: {ad_request.id}")
#         print(f"Campaign ID: {ad_request.campaign_id}")
#         if ad_request.campaign:
#             print(f"Campaign Title: {ad_request.campaign.title}")
#             print(f"Sponsor ID: {ad_request.campaign.sponsor_id}")
#             if ad_request.campaign.sponsor:
#                 print(f"Sponsor Company: {ad_request.campaign.sponsor.company_name}")
#             else:
#                 print("No sponsor associated with this campaign")
#         else:
#             print("No campaign associated with this AdRequest")
#         print("---")