use graph_reduction_evolution::*;
use rand::Rng;


use genevo::{
    operator::prelude::*, population::ValueEncodedGenomeBuilder, prelude::*, types::fmt::Display,
};



// const TARGET_TEXT: &str = "See how a genius creates a legend";
// const TARGET_TEXT: &str = "All the world's a stage, and all the men and women merely players: \
//                           they have their exits and their entrances; and one man in his time \
//                           plays many parts, his acts being seven ages.";

#[derive(Debug)]
struct Parameter {
    population_size: usize,
    generation_limit: u64,
    num_individuals_per_parents: usize,
    selection_ratio: f64,
    num_crossover_points: usize,
    mutation_rate: f64,
    reinsertion_ratio: f64,
}

impl Default for Parameter {
    fn default() -> Self {
        Parameter {
            population_size: 2000,
            generation_limit: 20000,
            num_individuals_per_parents: 10,
            selection_ratio: 0.3,
            num_crossover_points: 10,
            mutation_rate: 0.1,
            reinsertion_ratio: 0.6,
        }
    }
}

/// The phenotype
type Text = String;

/// The genotype
type Genome = Vec<u8>;

/// How do the genes of the genotype show up in the phenotype
trait AsPhenotype {
    fn as_text(&self) -> Text;
}

impl AsPhenotype for Genome {
    fn as_text(&self) -> Text {
        String::from_utf8(self.to_vec()).unwrap()
    }
}

/// The fitness function for `TextGenome`s.
#[derive(Clone, Debug)]
struct FitnessCalc;

impl FitnessFunction<Genome, i64> for FitnessCalc {
    fn fitness_of(&self, genome: &Genome) -> i64 {
        match Combinator::from_vector_repr(genome) {
            Ok(combinator) => {
                let mut result = 0;

                match combinator.clone().eval_with_recursion_limit(Some(10000)) {
                    Ok(x) => {
                        result += x.len() as i64 * 100;
                        result -= combinator.len() as i64 * 10;
                    }
                    Err(_) => {
                        // result -= 10000;
                    }
                }

                result.max(self.lowest_possible_fitness())
            }

            Err(_) => self.lowest_possible_fitness(),
        }
    }

    fn average(&self, fitness_values: &[i64]) -> i64 {
        (fitness_values.iter().sum::<i64>() as f64 / fitness_values.len() as f64) as i64
    }

    fn highest_possible_fitness(&self) -> i64 {
        1000000000
    }

    fn lowest_possible_fitness(&self) -> i64 {
        -1000000000
    }
}


// fn main() {
//     let params = Parameter::default();

//     let initial_population: Population<TextGenome> = build_population()
//         .with_genome_builder(ValueEncodedGenomeBuilder::new(TARGET_TEXT.len(), 32, 126))
//         .of_size(params.population_size)
//         .uniform_at_random();

//     let mut monkeys_sim = simulate(
//         genetic_algorithm()
//             .with_evaluation(FitnessCalc)
//             .with_selection(MaximizeSelector::new(
//                 params.selection_ratio,
//                 params.num_individuals_per_parents,
//             ))
//             .with_crossover(MultiPointCrossBreeder::new(params.num_crossover_points))
//             .with_mutation(RandomValueMutator::new(params.mutation_rate, 32, 126))
//             .with_reinsertion(ElitistReinserter::new(
//                 FitnessCalc,
//                 true,
//                 params.reinsertion_ratio,
//             ))
//             .with_initial_population(initial_population)
//             .build(),
//     )
//     .until(or(
//         FitnessLimit::new(FitnessCalc.highest_possible_fitness()),
//         GenerationLimit::new(params.generation_limit),
//     ))
//     .build();

//     println!("Starting Shakespeare's Monkeys with: {:?}", params);

//     loop {
//         let result = monkeys_sim.step();
//         match result {
//             Ok(SimResult::Intermediate(step)) => {
//                 let evaluated_population = step.result.evaluated_population;
//                 let best_solution = step.result.best_solution;
//                 println!(
//                     "Step: generation: {}, average_fitness: {}, \
//                      best fitness: {}, duration: {}, processing_time: {}",
//                     step.iteration,
//                     evaluated_population.average_fitness(),
//                     best_solution.solution.fitness,
//                     step.duration.fmt(),
//                     step.processing_time.fmt()
//                 );
//                 println!("      {}", best_solution.solution.genome.as_text());
//                 //                println!("| population: [{}]", result.population.iter().map(|g| g.as_text())
//                 //                    .collect::<Vec<String>>().join("], ["));
//             },
//             Ok(SimResult::Final(step, processing_time, duration, stop_reason)) => {
//                 let best_solution = step.result.best_solution;
//                 println!("{}", stop_reason);
//                 println!(
//                     "Final result after {}: generation: {}, \
//                      best solution with fitness {} found in generation {}, processing_time: {}",
//                     duration.fmt(),
//                     step.iteration,
//                     best_solution.solution.fitness,
//                     best_solution.generation,
//                     processing_time.fmt()
//                 );
//                 println!("      {}", best_solution.solution.genome.as_text());
//                 break;
//             },
//             Err(error) => {
//                 println!("{}", error);
//                 break;
//             },
//         }
//     }
// }
fn main() {
    /*
    const TRUE: Combinator = K;
    let FALSE = K.app(I);
    let NOT = S.app(S.app(I).app(K.app(FALSE.clone()))).app(K.app(TRUE.clone()));

    let mut expr = Y.app(Y);
    
    let mut rng = rand::thread_rng();
    for experiment in 0..5 {

        let mut x = Combinator::random_tree();
        while x.len() > 1000 {
            x = Combinator::random_tree();
        }

        println!("Tree #{} = {}", experiment, x);
        for trial in 0..10 {
            println!("\n\nTrial #{} for {}", trial, x);
            println!("{:?}", x.to_vector_repr());
            if let Ok(result) = Combinator::from_vector_repr(&x.to_vector_repr()) {
                println!("{}", result);
            }
            let y = x.clone().eval_with_recursion_limit(Some(10000));
            match y {
                Ok(result) => {
                    println!(" => {}", result);
                }
                Err(e) => {
                    println!("Error => {:?}", e);
                }
            }
            if let Ok(val) = x.church_numeral() {
                println!("Numeral: {}", val);
            }
            println!("Randomly mutating...");
            let mut n = rng.gen_range(0..x.len());
            println!("Selecting random combinator...");
            let replace = Combinator::random_combinator();
            println!("Replacing node #{} (of {}) with {}", n, x.len(), replace);
            x = x.replace_combinator(&mut n, replace);
        }
    }
     */
    
    let params = Parameter::default();

    let initial_population: Population<Genome> = build_population()
        .with_genome_builder(ValueEncodedGenomeBuilder::new(500, 0, 10))
        .of_size(params.population_size)
        .uniform_at_random();

    // let mut pop = vec![];
    // for i in 0..params.population_size {
    //     let mut genome = Combinator::random_tree();
    //     while genome.len() > 1000 {
    //         genome = Combinator::random_tree();
    //     }
    //     println!("Created genome #{} of {}", i + 1, params.population_size);
    //     println!("  => {}", genome);
    //     let mut result = vec![0; 1000];
    //     let repr = genome.to_vector_repr();
    //     result[..repr.len()].clone_from_slice(&repr);
        
    //     pop.push(result);
    // }
    // let initial_population: Population<Genome> = Population::with_individuals(pop);

    let mut monkeys_sim = simulate(
        genetic_algorithm()
            .with_evaluation(FitnessCalc)
            .with_selection(MaximizeSelector::new(
                params.selection_ratio,
                params.num_individuals_per_parents,
            ))
            .with_crossover(MultiPointCrossBreeder::new(params.num_crossover_points))
            .with_mutation(RandomValueMutator::new(params.mutation_rate, 0, 10))
            .with_reinsertion(ElitistReinserter::new(
                FitnessCalc,
                true,
                params.reinsertion_ratio,
            ))
            .with_initial_population(initial_population)
            .build(),
    )
    .until(or(
        FitnessLimit::new(FitnessCalc.highest_possible_fitness()),
        GenerationLimit::new(params.generation_limit),
    ))
    .build();

    println!("Starting Shakespeare's Monkeys with: {:?}", params);

    loop {
        let result = monkeys_sim.step();
        match result {
            Ok(SimResult::Intermediate(step)) => {
                let evaluated_population = step.result.evaluated_population;
                let best_solution = step.result.best_solution;
                println!(
                    "Step: generation: {}, average_fitness: {}, \
                     best fitness: {}, duration: {}, processing_time: {}",
                    step.iteration,
                    evaluated_population.average_fitness(),
                    best_solution.solution.fitness,
                    step.duration.fmt(),
                    step.processing_time.fmt()
                );
                println!("      {:?}", best_solution.solution.genome);
                if let Ok(genome) = Combinator::from_vector_repr(&best_solution.solution.genome) {
                    println!("      {}", genome);
                }
                //                println!("| population: [{}]", result.population.iter().map(|g| g.as_text())
                //                    .collect::<Vec<String>>().join("], ["));
            },
            Ok(SimResult::Final(step, processing_time, duration, stop_reason)) => {
                let best_solution = step.result.best_solution;
                println!("{}", stop_reason);
                println!(
                    "Final result after {}: generation: {}, \
                     best solution with fitness {} found in generation {}, processing_time: {}",
                    duration.fmt(),
                    step.iteration,
                    best_solution.solution.fitness,
                    best_solution.generation,
                    processing_time.fmt()
                );
                println!("      {:?}", best_solution.solution.genome);
                if let Ok(genome) = Combinator::from_vector_repr(&best_solution.solution.genome) {
                    println!("      {}", genome);
                }
                break;
            },
            Err(error) => {
                println!("{}", error);
                break;
            },
        }
    }
}