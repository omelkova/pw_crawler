This directory consists of all necessery code required to reproduce experiment on functionality diffusion based recommendation framwork for Web APIs.
* 'graph' subfolder stores rdf graphs. experiment_graph.ttl is a snapshot of the programmableweb repository at 22.10.2015 in turtle format. More details about the dataset can be found in 'analysis' subfolder. for_test_graph.ttl is a subgraph used for testing purposes.
* 'pw_crawler' subfolder contains code necessery to extract imformation from programmableweb repository and store it in RDF graph.
* 'analysis' subfolder contains ipython notebook script, which describe some main characteristics of experiment_graph.ttl as well as some characteristics related to infromation diffusion between Web APIs.
* 'experiment' subfolder contains code for functionality diffusion metric computation as well as matric's validation.

