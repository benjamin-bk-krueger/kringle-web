# kringle-web

## About

Kringle.info is an online CTF solution editor inspired by SANS Holiday Hack Challenge & KringleCon.  
SANS Holiday Hack Challenge happens each year and offers a lot of challenges, knowledge and fun. You can even submit a report containing your solutions and win prizes.  
In 2021 I have submitted a report in Markdown format (the ideal format in my opinion as it's easy and simple and offers code highlighting).  
I have invested some time to create that report so I thought it would be a good idea to automate that. Next I had the idea that even other people might find such an automation useful. I started creating a small Python script which resulted in a full web application based on Flask and some Flask modules.  
What does it currently offer?

- The application supports scenarios aka worlds which contain rooms and challenges (the SANS Holiday Hack Challenges are game based, also see chapter "Navigation")
- It does support different roles (world creators and registered users)
    - A world creator can upload (and later modify) a world and its rooms and challenges using a simple REST API
    - A registered user can submit and store a solution for each of the challenges
    - Submitted solutions can even be "liked"
- It does support registrations
    - There are invitation codes for world creators and registered users
    - I'm paying for the hardware so I don't want that to be abused
    - In the future I might find another way more useful
- It does support publication dates
    - The world creator can make a world public, before that point of time no one is able to see other solutions
    - The registered user can make each solution public, before that point of time no one is able to see it
- It does support S3 storage
    - Sometime you need to include images in your solutions, you can upload them to a S3 bucket and generate Markdown links
- It does support mail sending
    - Currently you'll get an e-mail if you have changed your password
    - That might be extended to other use cases, e.g. a world was made public
- It does support automatic report generation
    - You can generate a Markdown or HTML report containing all challenges and all your solutions
    - The report even contains clickable links and navigation

Currently it's still work in progress but quite stable and secure.
