query_rewrite="""<s>[INST] Rewrite the following user query to be short, simple, and clear. Preserve the original meaning.

Examples:

1. Original: how many days has the employee worked from the day he was hired.
   Rewritten: Number of days of the employee from today till the hired date.

2. Original: how many employees have joined the company in the year 2024, list them in descending order
   Rewritten: list all employees in descending order who joined in 2024

3. Original: list all the employees who is working in the company and has supervisor as Anand
   Rewritten: list all employees who have supervisor Anand

Now rewrite the following:

Original: {user_question}
Rewritten: [/INST]"""