# amp-Find and Delete DupeMacs
 Using the cisco amp api, return a list of computers that have duplicate macs. Target the macs that are the oldest and delte the corresponding guids from EDR.
## You will need:
 1. Access to the cisco api (https://api.amp.cisco.com/v1/) to provide:
    * Client ID
    * API Key
## Purpose
    This program will iterate through the computers in your cisco EDR environment and identify computers 
    that have duplicate MACs associated. Once identified, We only want to delete the least relevant GUIDs 
    (In the scope of this program,the computers that have check in the latest will be deleted and the most 
    recent one will be un-touched).
    
## Upcoming changes
    1. Clean up the UI side
    2. ~~Export details before/after delete command execution~~
    3. Cleanup existing functionality, etc.

### Example Find duplicates(Pre-Deletion) Log:
![pre_del](https://user-images.githubusercontent.com/108203246/176727656-d44e42f0-4fcd-41ae-a7ed-843f15a14680.PNG)

### Example Target GUIDs Log:
![target_guids](https://user-images.githubusercontent.com/108203246/176727911-6325b41e-483b-4700-9be7-83812c29e31d.PNG)
