// Instead of tree structure, we are going to use a vector of nodes which are fixed size.
// Each holds an optional parent index
// Each holds a vector of n keys
// Each holds a vector of either n+1 child indicies or n values

const FANOUT: usize = 5;
const SPLIT_AFTER: usize = FANOUT;
const MERGE: usize = FANOUT / 2;

fn borrow_mut_nodes<'a>(
    v: &'a mut Vec<ArrayNode>,
    indicies: (usize, usize, usize),
) -> (&mut ArrayNode, &mut ArrayNode, &mut ArrayNode) {
    let mut result: (
        Option<&mut ArrayNode>,
        Option<&mut ArrayNode>,
        Option<&mut ArrayNode>,
    ) = (None, None, None);

    let mut current: &mut [ArrayNode];
    let mut rest = &mut v[..];
    let mut index = 0;
    while rest.len() > 0 {
        (current, rest) = rest.split_at_mut(1);
        if index == indicies.0 {
            result.0 = Some(&mut current[0]);
        } else if index == indicies.1 {
            result.1 = Some(&mut current[0]);
        } else if index == indicies.2 {
            result.2 = Some(&mut current[0]);
        }
        index += 1;
    }
    (result.0.unwrap(), result.1.unwrap(), result.2.unwrap())
}

#[derive(Debug)]
enum NodeValue {
    Internal(Vec<usize>),
    Leaf(Vec<String>),
}

#[derive(Debug)]
struct ArrayNode {
    parent: Option<usize>,
    keys: Vec<String>,
    values: NodeValue,
}

impl ArrayNode {
    fn new() -> Self {
        ArrayNode {
            parent: None,
            keys: Vec::with_capacity(FANOUT),
            values: NodeValue::Leaf(Vec::with_capacity(FANOUT)),
        }
    }

    fn display(&self, indent: &str) {
        let parent_string = match self.parent {
            Some(index) => index.to_string(),
            None => "Root".to_string(),
        };

        let type_string = match self.values {
            NodeValue::Internal(_) => format!("{}Internal(parent: {})", indent, parent_string),
            NodeValue::Leaf(_) => format!("{}Leaf(parent: {})", indent, parent_string),
        };
        println!("{}Node: {}", indent, type_string);
        println!("{}Keys: {:?}", indent, self.keys);
        match self.values {
            NodeValue::Internal(ref children) => {
                println!("{}Children: {:?}", indent, children);
            }
            NodeValue::Leaf(ref values) => println!("{}Values: {:?}", indent, values),
        }
    }
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
            nodes: vec![ArrayNode::new()],
        }
    }

    fn display(&self) {
        let mut stack = vec![self.root_index];
        let mut indent = "".to_string();

        println!();
        println!("---------------------------------------------");
        println!("Displaying BTREE");
        println!("---------------------------------------------");

        loop {
            let mut next_stack = Vec::new();
            for node_index in stack.iter() {
                println!();
                self.nodes[*node_index].display(&indent);
                match self.nodes[*node_index].values {
                    NodeValue::Internal(ref pointers) => {
                        for pointer in pointers.iter() {
                            next_stack.push(*pointer);
                        }
                    }
                    NodeValue::Leaf(_) => (),
                }
            }

            if next_stack.len() == 0 {
                break;
            }

            stack = next_stack;
            indent += "  ";
        }
        println!();
    }

    fn check_split(&mut self, index: usize) {
        if self.nodes[index].keys.len() <= SPLIT_AFTER {
            return;
        }
        self.split(index);
    }

    fn split(&mut self, node_index: usize) {
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
        let promotion_key: String = mut_nodes_ref[node_index].keys[promotion_index].clone();

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
                    let mut sibling_pointers = Vec::with_capacity(FANOUT + 1);
                    sibling_pointers.extend(pointers.split_off(promotion_index + 1));

                    NodeValue::Internal(sibling_pointers)
                }
                NodeValue::Leaf(ref mut values) => {
                    let mut sibling_values = Vec::with_capacity(FANOUT);
                    sibling_values.extend(values.split_off(promotion_index));

                    NodeValue::Leaf(sibling_values)
                }
            },
        };
        mut_nodes_ref.push(sibling_node);

        // update parent of original node
        mut_nodes_ref[node_index].parent = Some(next_parent_index);

        //update parent node
        match parent {
            Some(parent_index) => {
                let parent_node = &mut mut_nodes_ref[parent.unwrap()];
                let mut key_position = 0;
                for key in parent_node.keys.iter() {
                    if key.clone() > promotion_key {
                        break;
                    }
                    key_position += 1;
                }
                parent_node.keys.insert(key_position, promotion_key);
                match parent_node.values {
                    NodeValue::Internal(ref mut pointers) => {
                        pointers.insert(key_position + 1, nodes_length);
                    }
                    NodeValue::Leaf(_) => panic!("Leaf node is parent"),
                }
                self.check_split(parent_index)
            }
            None => {
                // create new root node
                let mut new_root = ArrayNode {
                    parent: None,
                    keys: Vec::with_capacity(FANOUT),
                    values: NodeValue::Internal(Vec::with_capacity(FANOUT + 1)),
                };
                new_root.keys.push(promotion_key);

                match new_root.values {
                    NodeValue::Internal(ref mut pointers) => {
                        pointers.push(node_index);
                        pointers.push(self.nodes.len() - 1);
                    }
                    NodeValue::Leaf(_) => panic!("New root is a leaf"),
                }

                self.nodes.push(new_root);
                self.root_index = self.nodes.len() - 1;
            }
        };
    }

    fn remove_node(&mut self, index: usize) {
        // uses swap_remove so that we do not need to reorder all elements
        if self.root_index == index {
            panic!("Removed root node");
        }

        let swap_origin = self.nodes.len() - 1;

        self.nodes.swap_remove(index);

        if self.root_index == swap_origin {
            self.root_index = index;
        }

        // update parent indicies
        for node in self.nodes.iter_mut() {
            match node.values {
                NodeValue::Internal(ref mut pointers) => {
                    for pointer in pointers.iter_mut() {
                        if *pointer == index {
                            panic!("Removed referenced node");
                        }

                        if *pointer == swap_origin {
                            *pointer = index;
                        }
                    }
                }
                NodeValue::Leaf(_) => (),
            }
            match node.parent {
                Some(parent_index) => {
                    if parent_index == index {
                        panic!("Removed referenced node");
                    }
                    if parent_index == swap_origin {
                        node.parent = Some(index);
                    }
                }
                None => (),
            }
        }
    }

    fn check_merge(&mut self, index: usize) {
        let check_node = &self.nodes[index];

        match check_node.values {
            NodeValue::Internal(ref pointers) => {
                let mut first_pos = 0;
                let mut second_pos = 1;
                while second_pos < pointers.len() {
                    if self.nodes[pointers[first_pos]].keys.len()
                        + self.nodes[pointers[second_pos]].keys.len()
                        <= MERGE
                    {
                        self.merge(first_pos, second_pos);
                        return;
                    } else {
                        first_pos += 1;
                        second_pos += 1;
                    }
                }
            }
            NodeValue::Leaf(_) => {
                println!("Check merge called on leaf node --- noop")
            }
        }
    }

    fn merge(&mut self, left_node_index: usize, right_node_index: usize) {
        let parent_index = self.nodes[left_node_index].parent.clone().unwrap();

        let (left_node, right_node, parent_node) = borrow_mut_nodes(
            &mut self.nodes,
            (left_node_index, right_node_index, parent_index),
        );

        let parent_remove_separator = left_node.keys[left_node.keys.len() - 1].clone();

        let mut key_position = 0;
        for node_key in parent_node.keys.iter() {
            if node_key.clone() >= parent_remove_separator {
                break;
            }
            key_position += 1;
        }

        parent_node.keys.remove(key_position);
        match parent_node.values {
            NodeValue::Internal(ref mut pointers) => {
                pointers.remove(key_position);
            }
            NodeValue::Leaf(ref mut values) => {
                values.remove(key_position);
            }
        }

        // move keys and values from left node to right node
        right_node.keys.append(&mut left_node.keys);
        match right_node.values {
            NodeValue::Internal(ref mut pointers) => match left_node.values {
                NodeValue::Internal(ref mut left_pointers) => {
                    pointers.append(left_pointers);
                }
                NodeValue::Leaf(_) => panic!("Sibling nodes have different types"),
            },
            NodeValue::Leaf(ref mut values) => match left_node.values {
                NodeValue::Leaf(ref mut left_values) => {
                    values.append(left_values);
                }
                NodeValue::Internal(_) => panic!("Sibling nodes have different types"),
            },
        }

        // propagate merge upwards
        match parent_node.parent {
            Some(index) => self.check_merge(index),
            None => {}
        }

        self.remove_node(left_node_index);
    }

    fn get_node_for_key(&mut self, key: String) -> usize {
        let mut target_node = &mut self.nodes[self.root_index];
        let mut target_node_index = self.root_index;

        loop {
            match target_node.values {
                NodeValue::Internal(ref mut children) => {
                    // Find the index of the child to descend into
                    let mut index = 0;
                    for child in target_node.keys.iter() {
                        if *child == key {
                            break;
                        }
                        if *child > key {
                            break;
                        }
                        index += 1;
                    }
                    let next_index = children[index];

                    target_node = &mut self.nodes[next_index];
                    target_node_index = next_index;
                }
                NodeValue::Leaf(_) => {
                    // Insert into the leaf node
                    return target_node_index;
                }
            }
        }
    }

    fn insert(&mut self, key: String, value: String) {
        let target_node_index = self.get_node_for_key(key.clone());
        let target_node = &mut self.nodes[target_node_index];

        match target_node.values {
            NodeValue::Internal(_) => panic!("Search yielded internal node"),
            NodeValue::Leaf(ref mut children) => {
                // Insert into the leaf node
                let mut index = 0;
                let mut found = false;

                for child in target_node.keys.iter() {
                    if *child == key {
                        found = true;
                        break;
                    }
                    if *child > key {
                        break;
                    }
                    index += 1;
                }

                if found {
                    target_node.keys[index] = key;
                    children[index] = value;
                } else {
                    target_node.keys.insert(index, key);
                    children.insert(index, value);
                    if target_node.keys.len() > SPLIT_AFTER {
                        self.check_split(target_node_index)
                    }
                }
            }
        }
    }

    fn delete(&mut self, key: String) {
        let target_node_index = self.get_node_for_key(key.clone());

        let nodes = &mut self.nodes;
        let target_node = &mut nodes[target_node_index];

        match target_node.values {
            NodeValue::Internal(_) => panic!("Search yielded internal node"),
            NodeValue::Leaf(ref mut children) => {
                // Insert into the leaf node
                let mut index = 0;

                for child in target_node.keys.iter() {
                    if *child == key {
                        target_node.keys.remove(index);
                        children.remove(index);
                        break;
                    }
                    if *child > key {
                        break;
                    }
                    index += 1;
                }
            }
        }

        match target_node.parent {
            Some(index) => self.check_merge(index),
            None => {}
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
    tree.delete("a".to_string());
    tree.delete("b".to_string());
    tree.delete("d".to_string());
    tree.delete("e".to_string());
    tree.display();
    tree.delete("f".to_string());
    tree.display();
    tree.insert("k".to_string(), "k".to_string());
    tree.insert("l".to_string(), "l".to_string());
    tree.display();
}
