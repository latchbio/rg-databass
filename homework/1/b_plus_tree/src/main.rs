use std::cmp::{Eq, Ord, Ordering, PartialOrd};

#[derive(Debug)]
struct KeyValuePair {
    key: String,
    value: String,
}

#[derive(Debug)]
struct KeyPointerPair<'a> {
    key: Option<String>,
    pointer: &'a mut NodeType<'a>,
}

trait Insert {
    fn insert(&mut self, key: String, value: String);
}

#[derive(Debug)]
pub struct InternalNode<'a> {
    children: Vec<KeyPointerPair<'a>>,
}

impl<'a> InternalNode<'a> {
    pub fn new() -> Self {
        InternalNode {
            children: Vec::new(),
        }
    }
}

impl Insert for InternalNode<'_> {
    fn insert(&mut self, key: String, value: String) {
        let mut index = 0;
        for child in self.children.iter() {
            if child.key.is_none() {
                continue;
            }
            if child.key.clone().unwrap() > key {
                break;
            }
            index += 1;
        }

        match self.children.get_mut(index).unwrap().pointer {
            NodeType::Internal(node) => {
                node.insert(key, value);
            }
            NodeType::Leaf(node) => {
                node.insert(key, value);
            }
        }
    }
}

#[derive(Debug)]
pub struct LeafNode {
    children: Vec<KeyValuePair>,
}

impl<'a> LeafNode {
    pub fn new() -> Self {
        LeafNode {
            children: Vec::new(),
        }
    }
}

impl Insert for LeafNode {
    fn insert(&mut self, key: String, value: String) {
        let mut index = 0;
        let mut found = false;
        for child in self.children.iter() {
            if child.key == key {
                found = true;
                break;
            }
            if child.key > key {
                break;
            }
            index += 1;
        }

        if found {
            self.children.get_mut(index).unwrap().value = value;
        } else {
            self.children.insert(index, KeyValuePair { key, value });
        }
    }
}

#[derive(Debug)]
pub enum NodeType<'a> {
    Internal(InternalNode<'a>),
    Leaf(LeafNode),
}

#[derive(Debug)]
pub struct BPlusTree<'a> {
    root: NodeType<'a>,
    fanout: usize,
    // 0 <= merge_threshold <= split_threshold <= fanout
    split_threshold: usize, // node keys >= split_threshold => split
    merge_threshold: usize, // sum of two adjacent nodes <= merge_threshold => merge
}

impl<'a> BPlusTree<'a> {
    pub fn new(fanout: usize) -> Self {
        BPlusTree {
            root: NodeType::Leaf(LeafNode {
                children: Vec::new(),
            }),
            fanout,
            split_threshold: fanout,
            merge_threshold: fanout / 2,
        }
    }

    pub fn insert(&mut self, key: String, value: String) {
        match &mut self.root {
            NodeType::Internal(node) => {
                node.insert(key, value);
            }
            NodeType::Leaf(node) => {
                node.insert(key, value);
            }
        }
    }
}

fn main() {
    let mut tree = BPlusTree::new(3);
    tree.insert("a".to_string(), "a".to_string());
    tree.insert("a".to_string(), "b".to_string());
    println!("{:?}", tree);
}
