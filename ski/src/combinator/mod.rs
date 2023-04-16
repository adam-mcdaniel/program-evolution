use std::{sync::Arc, borrow::Borrow, fmt::{self, Debug, Display, Formatter}, collections::VecDeque};
use rand::prelude::*;
use petgraph::graph::{NodeIndex, UnGraph};
use petgraph::algo::{dijkstra, min_spanning_tree};
use petgraph::data::FromElements;
use petgraph::dot::{Dot, Config};

#[derive(Clone)]
pub enum Combinator {
    /// The S combinator.
    /// 
    /// S f g x = f x (g x)
    S {
        f: Option<Arc<Self>>,
        g: Option<Arc<Self>>,
    },
    /// The K combinator.
    /// 
    /// K x y = x
    K {
        x: Option<Arc<Self>>,
    },
    /// The I combinator.
    /// 
    /// I x = x
    I,
    // /// The Y combinator.
    // /// 
    // /// Y f = f (Y f)
    // Y,
    /// The W combinator.
    /// 
    /// W x = x x
    W,
    /// The B combinator.
    /// 
    /// B f g x = f (g x)
    B {
        f: Option<Arc<Self>>,
        g: Option<Arc<Self>>,
    },
    /// The C combinator.
    /// 
    /// C f g x = (f x) g
    C {
        f: Option<Arc<Self>>,
        g: Option<Arc<Self>>,
    },

    App(Arc<Self>, Arc<Self>),

    /// A combinator that is not a primitive combinator.
    Fun(String, Arc<dyn Fn(Self) -> Self>),
    Integer(i64),
}

pub const S: Combinator = Combinator::S { f: None, g: None };
pub const K: Combinator = Combinator::K { x: None };
pub const I: Combinator = Combinator::I;
// pub const Y: Combinator = Combinator::Y;
pub const W: Combinator = Combinator::W;
pub const B: Combinator = Combinator::B { f: None, g: None };
pub const C: Combinator = Combinator::C { f: None, g: None };


impl Combinator {
    pub fn app(self, other: Self) -> Self {
        Self::App(Arc::new(self), Arc::new(other))
    }

    pub fn eval(self) -> Result<Self, CombinatorError> {
        self.eval_with_recursion_limit(None)
    }

    pub fn eval_with_recursion_limit(self, recursion_limit: Option<usize>) -> Result<Self, CombinatorError> {
        safe_eval(self, recursion_limit)
    }

    pub fn fun(name: &str, f: impl Fn(Self) -> Self + 'static) -> Self {
        Self::Fun(name.to_string(), Arc::new(f))
    }

    pub fn church_numeral(&self) -> Result<Combinator, CombinatorError> {
        let f = |x: Self| {
            if let Self::Integer(i) = x {
                Self::Integer(i + 1)
            } else {
                x
            }
        };

        self.clone().app(Self::Fun("inc".to_string(), Arc::new(f))).app(Self::Integer(0)).eval_with_recursion_limit(Some(1000))
    }

    pub fn from_vector_repr(repr: &Vec<u8>) -> Result<Self, CombinatorError> {
        let mut stack: VecDeque<Self> = VecDeque::new();

        for i in repr {
            match i {
                1 => stack.push_back(S),
                2 => stack.push_back(K),
                3 => stack.push_back(I),
                // 4 => stack.push(Y),
                4 => stack.push_back(W),
                5 => stack.push_back(B),
                6 => stack.push_back(C),
                7 => {
                    if stack.len() < 2 {
                        // return Err(CombinatorError::InvalidVectorRepresentation(repr.clone()));
                        continue;
                    }
                    let f = stack.pop_front().unwrap();
                    let x = stack.pop_front().unwrap();
                    stack.push_front(f.app(x));
                }

                _ => {},
            }
        }
        if stack.is_empty() {
            return Err(CombinatorError::InvalidVectorRepresentation(repr.clone()));
        } else {
            return Ok(stack.pop_front().unwrap());
        }
    }

    // pub fn to_vector_repr(&self) -> Vec<u8> {
    //     let mut result = vec![];
    //     let mut stack: VecDeque<Self> = VecDeque::new();
    //     stack.push_back(self.clone());
    //     while let Some(combinator) = stack.pop() {
    //         match combinator {
    //             Self::S {..} => result.push(1),
    //             Self::K {..} => result.push(2),
    //             Self::I {..} => result.push(3),
    //             // Self::Y {..} => result.push(4),
    //             Self::W {..} => result.push(4),
    //             Self::B {..} => result.push(5),
    //             Self::C {..} => result.push(6),
    //             Self::App(f, x) => {
    //                 stack.push_back(clone(&x));
    //                 stack.push(clone(&y));
    //                 result.extend(&x.to_vector_repr());
    //                 result.extend(&y.to_vector_repr());
    //                 result.push(7);
    //             }
    //             _ => unreachable!(),
    //         }
    //     }
    //     result
    // }

    /// Generate a random combinator.
    pub fn random_combinator() -> Self {
        let mut rng = rand::thread_rng();
        match rng.gen_range(0..=60) {
            // 0..=5 => Y,
            0..=10 => B,
            11..=20 => K,
            21..=30 => I,
            31..=40 => W,
            41..=50 => S,
            51..=60 => C,
            // 0..=20 => K,
            // 21..=40 => I,
            // 41..=60 => S,
            _ => unreachable!(),
        }
    }

    /// Generate a random combinator expression.
    pub fn random_tree() -> Self {
        let mut rng = rand::thread_rng();

        let mut stack = Vec::new();

        let mut expr = Self::random_combinator();
        let mut count = rng.gen_range(1..=10);
        loop {
            if rng.gen_bool(0.3) {
                expr = expr.app(Self::random_combinator());
            } else {
                stack.push(expr);
                expr = Self::random_combinator();
            }

            if stack.is_empty() {
                if count == 0 {
                    break;
                }
                if rng.gen_bool(0.3) {
                    stack.push(Self::random_combinator());
                } else {
                    stack.push(expr);
                    stack.push(Self::random_combinator());
                    expr = Self::random_combinator();
                }
    
                count -= 1;
            }

            expr = stack.pop().unwrap().app(expr);
        }

        expr
    }


    /// Replace the nth combinator in the expression with the given combinator.
    pub fn replace_combinator(&self, n: &mut usize, combinator: Self) -> Self {
        match self {
            Self::App(f, x) => {
                let f = f.replace_combinator(n, combinator.clone());
                let x = x.replace_combinator(n, combinator.clone());
                f.app(x)
            }
            _ => {
                if *n == 0 {
                    combinator
                } else {
                    *n -= 1;
                    self.clone()
                }
            }
        }
    }

    pub fn len(&self) -> usize {
        match self {
            Self::App(f, x) => f.len() + x.len(),
            _ => 1,
        }
    }
}

#[derive(Clone)]
pub enum CombinatorError {
    RecursionLimitReached,
    InvalidCombinator(Combinator),
    InvalidApplication(Combinator, Combinator),
    InvalidVectorRepresentation(Vec<u8>),
}

impl Debug for CombinatorError {
    fn fmt(&self, f: &mut Formatter) -> fmt::Result {
        match self {
            Self::RecursionLimitReached => write!(f, "Recursion limit reached"),
            Self::InvalidCombinator(combinator) => write!(f, "Invalid combinator: {}", combinator),
            Self::InvalidApplication(g, x) => write!(f, "Invalid application: {} {}", g, x),
            Self::InvalidVectorRepresentation(repr) => write!(f, "Invalid vector representation: {:?}", repr),
        }
    }
}

fn app(x: Arc<Combinator>, y: Arc<Combinator>) -> Combinator {
    Combinator::App(x, y)
}

fn clone(x: &Arc<Combinator>) -> Combinator {
    let borrow: &Combinator = x.borrow();
    borrow.clone()
}


/// Evaluate a combinator expression.
/// 
/// # Examples
/// 
/// ```
/// use Combinator::{Combinator, S, K, I};
/// 
/// let expr = I.app(Combinator::I);
/// 
/// assert_eq!(expr.eval(), Combinator::I);
/// 
/// let expr = S.app(K).app(Combinator::I);
/// 
/// assert_eq!(expr.eval(), Combinator::K);
/// ```
fn safe_eval(mut expr: Combinator, recursion_limit: Option<usize>) -> Result<Combinator, CombinatorError> {
    // Tail recursion optimization with a loop.
    let mut recursion_count = 0;

    let mut argument_stack = Vec::new();

    loop {
        if let Some(limit) = recursion_limit {
            if recursion_count > limit {
                return Err(CombinatorError::RecursionLimitReached);
            }
        } else if recursion_count % 10000 == 10000 - 1 {
            eprintln!("Recursion count: {}", recursion_count);
        }

        match expr {
            Combinator::App(f, x) => {
                // Apply the function.
                match (clone(&f), x) {
                    // If the function is another application, first evaluate the function and then
                    // apply the arguments later.
                    (Combinator::App(f, x), y) => {
                        expr = clone(&f);
                        argument_stack.push(y.clone());
                        argument_stack.push(x);
                    }

                    // Apply the K combinator to the argument and return the result.
                    (Combinator::K { x }, y) => {
                        expr = match x {
                            // If an argument has already been supplied, return the result.
                            Some(x) => {
                                let borrow: &Combinator = x.borrow();
                                borrow.clone()
                            }
                            // Otherwise, save the argument and return the combinator.
                            None => Combinator::K { x: Some(y.clone()) }
                        }
                    }

                    // Apply the S combinator to the argument and return the result.
                    (Combinator::S { f, g }, x) => {
                        match (f, g) {
                            (None, None) => {
                                expr = Combinator::S { f: Some(x.clone()), g: None }
                            }

                            (Some(f), None) => {
                                expr = Combinator::S { f: Some(f.clone()), g: Some(x.clone()) }
                            }

                            (Some(f), Some(g)) => {
                                // let f = clone(&f);
                                // let g = clone(&g);
                                // expr = f.app(x.clone()).app(g.app(x));
                                expr = app(f.clone(), x.clone()).app(app(g.clone(), x.clone()));
                            }

                            (f, g) => {
                                let f = f.clone();
                                let g = g.clone();
                                return Err(CombinatorError::InvalidCombinator(Combinator::S { f, g }))
                            },
                        }
                    }

                    // Apply the B combinator to the argument and return the result.
                    (Combinator::B { f, g }, x) => {
                        match (f, g) {
                            (None, None) => {
                                expr = Combinator::B { f: Some(x.clone()), g: None }
                            }

                            (Some(f), None) => {
                                expr = Combinator::B { f: Some(f.clone()), g: Some(x.clone()) }
                            }

                            (Some(f), Some(g)) => {
                                expr = app(f.clone(), Arc::new(app(g.clone(), x.clone())));
                            }

                            (f, g) => {
                                let f = f.clone();
                                let g = g.clone();
                                return Err(CombinatorError::InvalidCombinator(Combinator::B { f, g }))
                            },
                        }
                    }

                    // Apply the C combinator to the argument and return the result.
                    (Combinator::C { f, g }, x) => {
                        match (f, g) {
                            (None, None) => {
                                expr = Combinator::C { f: Some(x.clone()), g: None }
                            }

                            (Some(f), None) => {
                                expr = Combinator::C { f: Some(f.clone()), g: Some(x.clone()) }
                            }

                            (Some(f), Some(g)) => {
                                // expr = f.app(x.clone()).app(g);
                                expr = app(Arc::new(app(f.clone(), x.clone())), g.clone());
                            }

                            (f, g) => {
                                let f = f.clone();
                                let g = g.clone();
                                return Err(CombinatorError::InvalidCombinator(Combinator::C { f, g }))
                            },
                        }
                    }

                    // Apply the I combinator to the argument and return the result.
                    (Combinator::I, x) => {
                        expr = clone(&x);
                    }

                    // Apply the Y combinator to the argument and return the result.
                    // (Combinator::Y, f) => {
                    //     expr = app(f.clone(), Arc::new(app(Arc::new(Combinator::Y), f.clone())));
                    // }

                    // Apply the W combinator to the argument and return the result.
                    (Combinator::W, f) => {
                        expr = app(f.clone(), f.clone());
                    }

                    (Combinator::Fun(_, f), x) => {
                        expr = f(clone(&x));
                    }

                    (f, _) => expr = f,
                }
            }
            _ => {
                if argument_stack.is_empty() {
                    return Ok(expr.clone())
                } else {
                    let x = argument_stack.pop().unwrap();
                    expr = app(Arc::new(expr), x);
                }
            },
        }

        recursion_count += 1;
    }
}

impl Display for Combinator {
    fn fmt(&self, formatter: &mut Formatter) -> fmt::Result {
        match self {
            Self::App(f, x) => {
                if let Self::App(g, y) = &**f {
                    write!(formatter, "({} {}) {}", g, y, x)?;
                } else if let Self::App(g, y) = &**x {
                    write!(formatter, "{} ({} {})", &f, g, y)?;
                } else {
                    write!(formatter, "{} {}", &f, &x)?;
                }
            }

            Self::K { x } => {
                write!(formatter, "K")?;
                if let Some(x) = x {
                    write!(formatter, "({})", x)?;
                }
            }

            Self::S { f, g } => {
                write!(formatter, "S")?;
                if let Some(f) = f {
                    write!(formatter, "({})", f)?;
                }
                if let Some(g) = g {
                    write!(formatter, "({})", g)?;
                }
            }

            Self::B { f, g } => {
                write!(formatter, "B")?;
                if let Some(f) = f {
                    write!(formatter, "({})", f)?;
                }
                if let Some(g) = g {
                    write!(formatter, "({})", g)?;
                }
            }

            Self::C { f, g } => {
                write!(formatter, "C")?;
                if let Some(f) = f {
                    write!(formatter, "({})", f)?;
                }
                if let Some(g) = g {
                    write!(formatter, "({})", g)?;
                }
            }

            Self::I => {
                write!(formatter, "I")?;
            }

            // Self::Y => {
            //     write!(formatter, "Y")?;
            // }

            Self::W => {
                write!(formatter, "W")?;
            }

            Self::Fun(name, _) => {
                write!(formatter, "{name}")?;
            }

            Self::Integer(x) => {
                write!(formatter, "{}", x)?;
            }
        }

        Ok(())
    }
}