import sys
import hidden
import hashlib
sys.path.append('/home/anton/.local/lib/python3.8/site-packages') 
sys.path.append('/home/anton/.local/lib/python3.8/site-packages/facebook_business-7.0.4.dist-info') 

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.customaudience import CustomAudience


from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.targetingsearch import TargetingSearch
from facebook_business.adobjects.targeting import Targeting
from facebook_business.adobjects.adimage import AdImage




my_app_id = hidden.my_app_id
my_app_secret = hidden.my_app_secret 
my_access_token = hidden.my_access_token
FacebookAdsApi.init(my_app_id, my_app_secret, my_access_token)
ad_account_id = hidden.ad_account_id

# ~ my_account = AdAccount(hidden.ad_account_id)
# ~ campaigns = my_account.get_campaigns()
# ~ print(campaigns)

# ~ #create custom audience
fields = [
]
params = {
  'name': 'My new Custom Audience',
  'subtype': 'CUSTOM',
  'description': 'People who did not finish buying tickets',
  'customer_file_source': 'USER_PROVIDED_ONLY',
}
custom_audience = AdAccount(hidden.ad_account_id).create_custom_audience(
  fields=fields,
  params=params,
)
print("custom audience created")


response = custom_audience.add_users(
    schema=CustomAudience.Schema.email_hash,
    users=[
        hashlib.sha256("anti_012@hotmail.com".encode('utf-8')).hexdigest(),
    ]
)
print("added myself to custom audience")


#creates ad campaign
params = {
  'name': 'My campaign',
  'objective': 'LINK_CLICKS',
  'status': 'PAUSED',
  'special_ad_categories': [],
}
campaign_result = AdAccount(ad_account_id).create_campaign(
  params=params,
)
print("ad campaign created")



#this ain't it chief
adset = AdSet(parent_id=ad_account_id)
adset.update({    
    'name': 'My adset',    
    'campaign_id': campaign_result["id"],    
    'daily_budget': 150,    
    'billing_event': 'CLICKS',    
    'optimization_goal': 'IMPRESSIONS',    
    'bid_amount': 10,    
    #'targeting': {'geo_locations': {'countries': {'TR'}},      'publisher_platforms': 'facebook'},    
    #'start_time': 'ENTER START DATE HERE',    
    #'end_time': 'ENTER END DATE HERE',
})
adset.remote_create(params={'status': 'PAUSED'})
print("adset created")





image = AdImage(parent_id=ad_account_id)
image[AdImage.Field.filename] = 'fisk.jpeg'
image.remote_create() 
image_hash = image[AdImage.Field.hash]
print("image uploaded")

fields = []
params = {  
    'name': 'test_adset',  
    'object_story_spec' : {'page_id' : page_id, 'link_data' :
        {'image_hash' : image_hash, 'link' : 'www.google.com' , 'message' : 'try it out'}}, }
adcreative = AdAccount(ad_account_id).create_ad_creative(fields=fields, params=params)
print("adcreative done")


fields = []
params = {  
    'name' : 'test_ad',  
    'adset_id' : adset['id'],  
    'creative' : {'creative_id': adcreative['creative_id']},
    'status' : 'PAUSED',
    'audience_id' : custom_audience[id]} #det här kanske är bra??
AdAccount(ad_account_id).create_ad(fields=fields, params=params)
print("ad created")




