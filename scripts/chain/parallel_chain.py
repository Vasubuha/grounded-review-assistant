from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel

load_dotenv()

model1 = ChatGroq(
    model="openai/gpt-oss-120b",  # strong + supports tool calling
    temperature=0
)

model2  = ChatGroq(
    model = "qwen/qwen3-32b",
    temperature=0
)

prompt1 = PromptTemplate(
    template = "Generate short and simple notes from following text: {text}",
    input_variables = ["text"]
)

prompt2 = PromptTemplate(
    template= "Generate a short question and answer from following text : {text}",
    input_variables=["text"]
)

prompt3 = PromptTemplate(
    template = "Merge the provided notes and quiz into a single document \n notes -> {notes} and quiz -> {quiz}",
    input_variables=['notes', 'quiz']
)

parser = StrOutputParser()

parallel_chain = RunnableParallel({
    'notes' : prompt1 | model1 | parser,
    'quiz' : prompt2 | model2 | parser
})

merge_chain = prompt3 | model1 | parser

chain = parallel_chain | merge_chain

text = """
Linear Regression is a fundamental supervised learning algorithm used to model the relationship between a dependent variable and one or more independent variables. It predicts continuous values by fitting a straight line that best represents the data.

It assumes that there is a linear relationship between the input and output
Uses a best‑fit line to make predictions
Commonly used in forecasting, trend analysis, and predictive modelling 
introduction_to_linear_reg.webp

For example we want to predict a student's exam score based on how many hours they studied. We observe that as students study more hours, their scores go up. In the example of predicting exam scores based on hours studied. Here

Independent variable (input): Hours studied because it's the factor we control or observe.
Dependent variable (output): Exam score because it depends on how many hours were studied.
We use the independent variable to predict the dependent variable.

Best Fit Line in Linear Regression
In linear regression, the best-fit line is the straight line that most accurately represents the relationship between the independent variable (input) and the dependent variable (output). It is the line that minimizes the difference between the actual data points and the predicted values from the model.

1. Goal of the Best-Fit Line
The goal of linear regression is to find a straight line that minimizes the error (the difference) between the observed data points and the predicted values. This line helps us predict the dependent variable for new, unseen data.
Here Y is called a dependent or target variable and X is called an independent variable also known as the predictor of Y.

\theta_1 represents the intercept, which is the value of Y when X = 0
\theta_2 represents the slope, which shows how much Y changes for a unit change in X
There are many types of functions or modules that can be used for regression. A linear function is the simplest type of function. Here, X may be a single feature or multiple features representing the problem.
"""

result = chain.invoke({"text": text})
print(result)

visual = chain.get_graph().print_ascii()