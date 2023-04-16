// mod combinator;

pub enum Combinator {
    S,
    K,
    I,
    B,
    C,
    W,
    Y,
}


pub enum Subexpr {
    Combinator(Combinator),
    Apply,
}

pub struct Expr {
    pub subexprs: Vec<Subexpr>
}

impl Expr {
    pub fn new() -> Expr {
        Expr { subexprs: Vec::new() }
    }

    pub fn push(&mut self, subexpr: Subexpr) {
        self.subexprs.push(subexpr);
    }

    pub fn pop(&mut self) -> Option<Subexpr> {
        self.subexprs.pop()
    }

    pub fn len(&self) -> usize {
        self.subexprs.len()
    }

    pub fn is_empty(&self) -> bool {
        self.subexprs.is_empty()
    }

    pub fn simplify(&self) -> Result<Self, String> {
        

    }
}