# Shareify 1.2.0 - The "Data Control" Update

## What's New This Time

Been working on the cloud bridge infrastructure and honestly, it needed some serious database management tools. This update brings proper admin controls for when things get messy.

### iOS App Actually Previews Files Now

File preview in the iOS app finally works properly. No more downloading PDFs just to see if it's the right document. Images, text files, even code files render correctly. Took way longer than it should've but it's solid now.

### iOS App Polish

The iOS app got some visual love with proper SOM styling. Looks more cohesive now instead of like three different apps stitched together. Also fixed some of the wonky animations that made it feel janky.

### Cloud Bridge Database Management

Finally built a proper interface for managing user data on the bridge. Two flavors:


### Better Authentication Flow

The token-based auth got a major cleanup:
- Automatic fallback when tokens expire (no more manual re-auth)
- Persistent authentication state across reconnections  
- Better error handling when the bridge can't reach your server

### Cloud Account Registration

You can now sign up for cloud bridge accounts directly from your local dashboard. No more emailing me for access or messing around with manual account creation. Just enter your details and you're good to go.


### Cloud Bridge Improvements

- Real-time activity monitoring in the dashboard
- Server health metrics that actually update
- Proper user management with role-based access
- Bridge metadata visualization (finally know what's happening under the hood)

## What Got Fixed

- iOS file preview actually works now (was completely broken before)
- Cloud connection stability - fewer random disconnects
- Authentication tokens don't randomly invalidate anymore
- Database operations are way faster (proper indexing this time)
- Better error messages when bridge setup fails
- Fixed the weird delay when commands executed through cloud
- SOM styling inconsistencies in the iOS app


## Notes

You'll need to update both your local server and any iOS apps. The new authentication flow isn't backwards compatible with 1.1.x.

The database management tools are admin-only right now. If you need access and don't have the bridge dashboard password, that's intentional.
