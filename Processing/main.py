from json import load
import graph_creation
import load_model
import encoder

if __name__ == "__main__":
    # intialize the grpah cretaion object
    g = graph_creation.Graph()

    # retrieve the news url to predit for
    news_url = input("Input new urls : ")

    # get the graph of the news_url propogation in twitter
    G, news_data = g.get_graph_of_news_url(news_url)

    # enocde the data using users last 200 tweets and profile features
    e = encoder.Encoder()   # initialize the encoder object 
    inputToGNN = e.getInputToModel(G, news_data)
    print(type(inputToGNN))
    print(inputToGNN.shape)
    # loading the torch GNN model
    model = load_model.load_model()

    # getting processded egde index
    edge_index = load_model.get_processed_data(graph=G)
    print(edge_index)
    # predit the label

    prediction = load_model.predict_all(model = model,data= inputToGNN,edge_index=edge_index)

    # return the label and graph
    print(prediction)
