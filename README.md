## Motivations

I initially wanted to get good statistics about the number of startups from
different universities. On thinking about it a bit, I realised that we can
answer much richer queries like `startups from college X in city Y with at
least one round of funding` if we store the data in an appropriate graph
database format.

Also, I am particularly interested in implementing a quick and crude version of
the system myself, so the learning is another motivation.

## Alumni-network feature in angel.co
Once I set out planning this project, I took a thorough look at the website, to
find that there already is an alumni listing with profession on angel.co. It is
a new feature.

For now, I am not thinking about using those lists, because all the information
that I need is already obtainable without it.


# Database choice
NoSQL because there is no rigid structure to our entities. For instance, a
company may have any number of employees, founders, or seed rounds, etc.
