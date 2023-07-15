// Instead of tree structure, we are going to use a vector of nodes which are fixed size.
// Each holds an optional parent index
// Each holds a vector of n keys
// Each holds a vector of either n+1 child indicies or n values

const FANOUT: usize = 3;
const SPLIT_AFTER: usize = FANOUT;
const MERGE_AFTER: usize = FANOUT / 2;

#[derive(Debug)]
enum NodeValue {
    Internal(Vec<Option<usize>>),
    Leaf(Vec<Option<String>>),
}

#[derive(Debug)]
struct ArrayNode {
    parent: Option<usize>,
    keys: Vec<Option<String>>,
    values: NodeValue,
}

#[derive(Debug)]
struct BPlusTree {
    root_index: usize,
    nodes: Vec<ArrayNode>,
}

impl BPlusTree {
    fn new() -> Self {
        BPlusTree {
            root_index: 0,
            nodes: vec![ArrayNode {
                parent: None,
                keys: Vec::new(),
                values: NodeValue::Leaf(Vec::new()),
            }],
        }
    }

    fn split(&mut self, node_index: usize) {
        if self.nodes[node_index].keys.len() <= SPLIT_AFTER {
            println!(
                "Node {} has {} keys, not splitting",
                node_index,
                self.nodes[node_index].keys.len()
            );
            return;
        }

        println!("Splitting node {}", node_index);
        println!("Original node: {:?}", self.nodes[node_index]);

        let nodes_length = self.nodes.len();
        let mut_nodes_ref = &mut self.nodes;
        let parent = mut_nodes_ref[node_index].parent;
        let next_parent_index = match parent {
            Some(index) => index,
            None => {
                // create new root node
                mut_nodes_ref.len() + 1
            }
        };

        // determine promotion index
        let promotion_index = match mut_nodes_ref[node_index].values {
            NodeValue::Internal(_) => FANOUT / 2,
            NodeValue::Leaf(_) => (FANOUT + 1) / 2,
        };
        let promotion_key: String = mut_nodes_ref[node_index].keys[promotion_index]
            .clone()
            .unwrap();

        println!("Promotion index: {}", promotion_index);
        println!("Promotion key: {}", promotion_key);

        let mut right_keys = mut_nodes_ref[node_index].keys.split_off(promotion_index);
        match mut_nodes_ref[node_index].values {
            NodeValue::Internal(_) => {
                right_keys.remove(0);
            }
            NodeValue::Leaf(_) => (),
        }

        // create sibling node
        let sibling_node = ArrayNode {
            parent: Some(next_parent_index),
            keys: right_keys,
            values: match mut_nodes_ref[node_index].values {
                NodeValue::Internal(ref mut pointers) => {
                    NodeValue::Internal(pointers.split_off(promotion_index + 1))
                }
                NodeValue::Leaf(ref mut values) => {
                    NodeValue::Leaf(values.split_off(promotion_index))
                }
            },
        };
        mut_nodes_ref.push(sibling_node);

        // update parent of original node
        mut_nodes_ref[node_index].parent = Some(next_parent_index);

        println!("Original node: {:?}", mut_nodes_ref[node_index]);
        println!("Sibling node: {:?}", mut_nodes_ref[nodes_length]);

        //update parent node
        match parent {
            Some(parent_index) => {
                let parent_node = &mut mut_nodes_ref[parent.unwrap()];
                let mut key_position = 0;
                for key in parent_node.keys.iter() {
                    if key.is_none() {
                        break;
                    }
                    if key.clone().unwrap() > promotion_key {
                        break;
                    }
                    key_position += 1;
                }
                parent_node.keys.insert(key_position, Some(promotion_key));
                match parent_node.values {
                    NodeValue::Internal(ref mut pointers) => {
                        pointers.insert(key_position + 1, Some(nodes_length));
                    }
                    NodeValue::Leaf(_) => panic!("Leaf node is parent"),
                }
                self.split(parent_index)
            }
            None => {
                // create new root node
                let new_root = ArrayNode {
                    parent: None,
                    keys: vec![Some(promotion_key)],
                    values: NodeValue::Internal(vec![Some(node_index), Some(self.nodes.len() - 1)]),
                };
                self.nodes.push(new_root);
                self.root_index = self.nodes.len() - 1;
            }
        };
    }

    fn insert(&mut self, key: String, value: String) {
        let mut target_node = &mut self.nodes[self.root_index];
        let mut target_node_index = self.root_index;

        loop {
            match target_node.values {
                NodeValue::Internal(ref mut children) => {
                    // Find the index of the child to descend into
                    let mut index = 0;
                    for child in target_node.keys.iter() {
                        let child = match child {
                            Some(key) => key,
                            None => break,
                        };

                        if *child == key {
                            break;
                        }
                        if *child > key {
                            break;
                        }
                        index += 1;
                    }
                    let next_index = match children[index] {
                        Some(index) => index,
                        None => panic!("Internal node has no child at index {}", index),
                    };

                    target_node = &mut self.nodes[next_index];
                    target_node_index = next_index;
                }
                NodeValue::Leaf(ref mut children) => {
                    // Insert into the leaf node
                    println!("Inserting key {} and value {}", key, value);

                    let mut index = 0;
                    let mut found = false;

                    for child in target_node.keys.iter() {
                        let child = match child {
                            Some(key) => key,
                            None => break,
                        };

                        if *child == key {
                            found = true;
                            break;
                        }
                        if *child > key {
                            break;
                        }
                        index += 1;
                    }

                    println!("Index: {}", index);

                    if found {
                        target_node.keys[index] = Some(key);
                        children[index] = Some(value);
                    } else {
                        target_node.keys.insert(index, Some(key));
                        children.insert(index, Some(value));
                        if target_node.keys.len() > SPLIT_AFTER {
                            self.split(target_node_index)
                        }
                    }
                    break;
                }
            }
        }
    }
}

fn main() {
    let mut tree = BPlusTree::new();
    tree.insert("a".to_string(), "a".to_string());
    tree.insert("b".to_string(), "b".to_string());
    tree.insert("c".to_string(), "c".to_string());
    tree.insert("d".to_string(), "d".to_string());
    tree.insert("e".to_string(), "e".to_string());
    tree.insert("f".to_string(), "f".to_string());
    tree.insert("g".to_string(), "g".to_string());
    tree.insert("h".to_string(), "h".to_string());
    tree.insert("i".to_string(), "i".to_string());
    tree.insert("j".to_string(), "j".to_string());
    println!("{:?}", tree);
}
