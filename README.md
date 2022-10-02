# PayBack
Fake News Detection as a Service, built with the State-Of-The-Art User Preference Aware GNNs

## Product Description
Here we harness the power of Graph Neural Networks (GNNs) for solving the problem of Fake News Detection. We utilise information regarding both the spread of fake news over twitter via propogation graphs and the user preferences via past tweets to make a prediction about the veracity of a web article.

![alt text](https://github.com/DChops/PayBack/blob/main/Graph.png?raw=true)

## Usage

### WebApp
You can acceess the free online webapp at :

### API
For developers seeking an endpoint for classifying articles as real or fake using their Web URLS, use the API endpoint as follows:
- http://www.delphipayback.com/

## Datasets
We utilised the Politifact & Gossicop Datasets available publicly using the UPFD() class in pytorch_geometric.datasets.

A brief summary of the datasets is as follows:
| Data  | #Graphs  | #Fake News| #Total Nodes  | #Total Edges  | #Avg. Nodes per Graph  |
|-------|--------|--------|--------|--------|--------|
| Politifact | 314   |   157    |  41,054  | 40,740 |  131 |
| Gossipcop |  5464  |   2732   |  314,262  | 308,798  |  58  |

Both Politfact & Gossicop are graph-based datasets curated by Yingtong et al. at https://github.com/safe-graph/GNN-FakeNews/blob/main using the data in FakeNewsNet at https://github.com/KaiDMML/FakeNewsNet

<a href="https://www.politifact.com">Politifact</a>: A website that labels political news articles as real or fake

<a href="https://www.suggest.com">Gossicop</a>(Renamed to Suggest): A website that labels celebrity news articles as real or fake


## Research Papers Referenced
<ul>
  <li> Yingtong Dou et al., "User Preference Aware Fake News Detection", July 2021, Retrieved via: https://arxiv.org/abs/2104.12259
  <li> Yi Han et al., "Graph Neural Networks with Continual Learning for Fake News Detection from Social Media", August 2020, Retrieved via: https://arxiv.org/abs/2007.03316
  <li> Rex Ying et al., "Hierarchical Graph Prepresentation Learning with Differentiable Pooling", Feb 2019, Retrieved via: https://arxiv.org/abs/1806.08804
<ul>
